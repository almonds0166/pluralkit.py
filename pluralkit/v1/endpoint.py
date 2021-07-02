
import asyncio
import functools

def func(f):
   """Makes an asynchronous `Client` function synchronous if `Client.async_mode` == ``False``.
   """
   @functools.wraps(f)
   def wrapper(*args, **kwargs):
      self = args[0]

      # save an asynchronous copy! if not yet saved
      async_name = "_" + f.__name__
      if async_name not in self._async:
         setattr(self, async_name, f)
         self._async.add(async_name)

      awaitable = f(*args, **kwargs)
      if self.async_mode:
         return awaitable

      loop = asyncio.get_event_loop()
      result = loop.run_until_complete(awaitable)
      return result

   return wrapper

def iter(f):
   """Makes an asynchronous `Client` iterator synchronous if `Client.async_mode` == ``False``.
   """
   @functools.wraps(f)
   def wrapper(*args, **kwargs):
      self = args[0]

      # save an asynchronous copy! if not yet saved
      async_name = "_" + f.__name__
      if async_name not in self._async:
         setattr(self, async_name, f)
         self._async.add(async_name)

      awaitable = f(*args, **kwargs)
      if self.async_mode:
         return awaitable

      async def flatten(awaitable):
         return [item async for item in awaitable]

      loop = asyncio.get_event_loop()
      result = loop.run_until_complete(flatten(awaitable))
      return result

   return wrapper