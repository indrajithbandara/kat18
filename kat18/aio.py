"""
Because I don't want to block the coroutine event loop, I have written a
fairly crappy implementation of a system to run IO tasks on a new thread
safely. The issue is, I don't want to have to write code to interface with
the files in each cog I need to use it, so I am writing some crappy
work-around class to implement globally in the class in client.py
"""
import copy
import io
import json
import os
import time

import asyncio
import traceback
import typing


class AsyncFile:
    """Provides an interface to read and write to/from the file."""
    def __init__(self, file_name):
        """
        Makes an async file pointer object.
        :param file_name: the location of the file.
        """
        # Hide this so the user cannot alter it. Use a property
        # to provide read-only access.
        self.__file_name = file_name
        self._lock = asyncio.Lock()

    @property
    def file_name(self):
        """Gets the file name."""
        return self.__file_name

    async def execute(self, func, mode, loop=None):
        """
        Executes function on the event loop. Passes the

        However, any args and kwargs passed to this method barr :attr:`mode`
        are also passed to this function after the file pointer is.

        :attr:`fp` is just the file pointer obtained using :attr:`open()`
        from the python builtins.

        :param func: the function to call on another thread.
        :param mode: the mode to access the file in.
        :param loop: the event loop to use if not None, else let asyncio
                use the default loop.
        :return: the result of executing the function that was passed.
        """
        with await self._lock:
            # We ensure to open the file on the same thread we are
            # executing the function on, as I am unsure if the open()
            # method provides any kind of thread safety.
            def do_io(_func, file_name, _mode):
                # noinspection PyBroadException
                try:
                    with open(file_name, mode=_mode) as fp:
                        return _func(fp)
                except BaseException:
                    traceback.print_exc()
                    return None

            if loop is None:
                loop = asyncio.get_event_loop()

            return await loop.run_in_executor(
                None,
                do_io,
                func,
                self.file_name,
                mode
            )


class AsyncJsonValue:
    """
    Hooks to a JSON file and updates the contents of that JSON file
    when this value is SET. This is done asynchronously.

    The constructor should be done in a synchronous context, as it initially
    reads the file in without dispatching to any thread pool executor. This is
    done primarily because if defined in a constructor, event loops may not
    yet be initialised.
    """
    def __init__(self, file_name, default_value):
        self.__async_file = AsyncFile(file_name)

        # Yes, this blocks.
        if not os.path.exists(file_name):
            with open(file_name, 'w') as f:
                json.dump(obj=default_value, fp=f, indent=' ' * 4)

        with open(file_name) as f:
            self.__cached = json.load(f)

    def get(self):
        """Gets the value."""
        return copy.deepcopy(self.__cached)

    async def set(self, value):
        """Sets the value."""
        self.__cached = await self.__serialize(value)

    def set_blocking(self, value):
        """Sets the value, but blocks until it is complete."""
        future: asyncio.Future = asyncio.ensure_future(self.set(value))

        while not future.done():
            # Sufficient to allow this thread to yield another thread. This
            # just causes the system to sleep for a little while longer until
            # the event loop is complete with whatever it is doing.
            time.sleep(0.001)

    @property
    def cached_value(self):
        """
        Gets the raw cached value. This should only be used IF you are
        not going to mutate the value inside if it is a collection. If you do
        modify it, then behaviour is undefined and stuff may well break or
        become inconsistent.
        """
        return self.__cached

    def __iter__(self):
        return self.get().__iter__()

    def __contains__(self, item):
        return self.get().__contains__(item)

    def __eq__(self, other):
        return self.get().__eq__(other)

    async def __serialize(self, value):
        """Serializes the given value to the JSON file by overwriting."""
        sfp = io.StringIO()
        json.dump(obj=value, fp=sfp, indent=' ' * 4)
        # Seek to the start of the stringio fp.
        sfp.seek(0)

        def write(fp):
            fp.write(sfp.read())

        await self.__async_file.execute(func=write, mode='w')
        return value

    def read_from_file(self) -> typing.Coroutine:
        """
        Rereads from the file. This returns a coroutine that must be
        awaited or ensured as a future.
        """
        def read(fp):
            return json.load(fp=fp)
        return self.__async_file.execute(func=read, mode='r')
