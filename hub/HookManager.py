import os
import logging

class InvalidHookError(Exception):
	"""A module has tried to access a hook for an unknown function."""


class Hook(object):
	"""A conditional hook that overrides or modifies Hub behavior.

	Each Hook corresponds to a single Python callable that may be overridden
	by the hook system. Multiple Hooks may inspect or modify the parameters, but
	only a single callable may elect to actually handle the call. The inspect()
	method will be called for each hook in the order the hooks are imported
	by the HookManager. The final set of parameters will be passed to the
	targetted hook's __call__() method. If more than one Hook elects to execute
	a hooked function, a warning logging message be issued and the *first* Hook
	encountered will be executed.
	"""

	def inspect(self, args, kwargs):
		"""Inspects a hooked function's parameters, possibly modifying them.

		Args:
			args: List of positional arguments for the hook call.
			kwargs: Dictionary of keyword arguments for the hook call.

		Returns:
			True if this Hook should handle the call, False otherwise.
		"""
		return False

	def __call__(self, *args, **kwargs):
		"""Handles the hook call.

		Args:
			*args, **kwargs: Parameters matching the original function's signature.

		Returns:
			The return value expected by the original function.
		"""
		assert False, '__call__ method not defined for %s' % self.__class__


class HookManager(object):
	"""Manages registering and loading Hooks from external modules.

	Hook modules will have a copy of this 'main' module's contents in their
	globals dictionary and the Hooks class to be sub-classed. They will also
	have the 'register' method, which the hook module should use to register any
	Hook sub-classes that it defines.

	The 'register' method has the same signature as the _register method of
	this class, but without the leading 'filename' argument; that value is
	curried by the HookManager.
	"""

	def __init__(self):
		"""Initializer."""
		# Maps hook functions to a list of (filename, Hook) tuples.
		self._mapping = {}

	def load(self, hooks_path='hooks', globals_dict=None):
		"""Loads all hooks from a particular directory.

		Args:
			hooks_path: Optional. Relative path to the application directory or
				absolute path to load hook modules from.
			globals_dict: Dictionary of global variables to use when loading the
				hook module. If None, defaults to the contents of this 'main' module.
				Only for use in testing!
		"""
		if globals_dict is None:
			globals_dict = globals()

		hook_directory = os.path.join(os.getcwd(), hooks_path)
		logging.info(hook_directory)
		module_list = os.listdir(hook_directory)
		for module_name in sorted(module_list):
			if not module_name.endswith('.py'):
				continue
			module_path = os.path.join(hook_directory, module_name)
			context_dict = globals_dict.copy()
			context_dict.update({
				'Hook': Hook,
				'register': lambda *a, **k: self._register(module_name, *a, **k)
			})
			logging.debug('Loading hook "%s" from %s', module_name, module_path)
			try:
				exec open(module_path) in context_dict
			except:
				logging.exception('Error loading hook "%s" from %s',
													module_name, module_path)
				raise

	def declare(self, original):
		"""Declares a function as being hookable.

		Args:
			original: Python callable that may be hooked.
		"""
		self._mapping[original] = []

	def execute(self, original, *args, **kwargs):
		"""Executes a hookable method, possibly invoking a registered Hook.

		Args:
			original: The original hooked callable.
			args: Positional arguments to pass to the callable.
			kwargs: Keyword arguments to pass to the callable.

		Returns:
			Whatever value is returned by the hooked call.
		"""
		try:
			hook_list = self._mapping[original]
		except KeyError, e:
			raise InvalidHookError(e)

		modifiable_args = list(args)
		modifiable_kwargs = dict(kwargs)
		matches = []
		for filename, hook in hook_list:
			logging.debug('Inspecting args for %s by hook from module %s: '
										'args=%r, kwargs=%r', original, filename,
										modifiable_args, modifiable_kwargs)
			if hook.inspect(modifiable_args, modifiable_kwargs):
				matches.append((filename, hook))

		filename = __name__
		designated_hook = original
		if len(matches) >= 1:
			filename, designated_hook = matches[0]
			logging.debug('Using matched hook for %s from module %s',
										original, filename)

		if len(matches) > 1:
			logging.critical(
					'Found multiple matching hooks for %s in files: %s. '
					'Will use the first hook encountered: %s',
					original, [f for (f, hook) in matches], filename)

		return designated_hook(*args, **kwargs)

	def _register(self, filename, original, hook):
		"""Registers a Hook to inspect and potentially execute a hooked function.

		Args:
			filename: The name of the hook module this Hook is defined in.
			original: The Python callable of the original hooked function.
			hook: The Hook to register for this hooked function.

		Raises:
			InvalidHookError if the original hook function is not known.
		"""
		try:
			self._mapping[original].append((filename, hook))
		except KeyError, e:
			raise InvalidHookError(e)

	def override_for_test(self, original, test):
		"""Adds a hook function for testing.

		Args:
			original: The Python callable of the original hooked function.
			test: The callable to use to override the original for this hook function.
		"""
		class OverrideHook(Hook):
			def inspect(self, args, kwargs):
				return True
			def __call__(self, *args, **kwargs):
				return test(*args, **kwargs)
		self._register(__name__, original, OverrideHook())

	def reset_for_test(self, original):
		"""Clears the configured test hook for a hooked function.

		Args:
			original: The Python callable of the original hooked function.
		"""
		self._mapping[original].pop()