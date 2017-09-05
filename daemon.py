import sys, os, time, atexit, signal

class daemon:
	"""A generic daemon class.

	Usage: subclass the daemon class and override the run() method."""

	def __init__(self, pidfile): self.pidfile = pidfile

	def daemonize(self):
		try:
			if os.fork() > 0:
				sys.exit(0)
		except OSError as err:
			sys.exit("fork #1 failed: {0}\n".format(err))

		os.chdir('/')
		os.setsid()
		os.umask(0)

		try:
			if os.fork() > 0:
				sys.exit(0)
		except OSError as err:
			sys.exit("fork #2 failed: {0}\n".format(err))

		def delpid():
			if os.path.exists(self.pidfile):
				os.remove(self.pidfile)

		atexit.register(delpid)

		with open(self.pidfile, 'w') as f:
			f.write(str(os.getpid()))
			f.flush()

	def start(self):
		"""Start the daemon."""
		if os.path.exists(self.pidfile):
			sys.exit("Error: pidfile \"{}\" already exists!".format(self.pidfile))
		
		self.daemonize()
		self.run()

	def stop(self):
		"""Stop the daemon."""
		if not os.path.exists(self.pidfile):
			sys.stderr.write("Warning: pidfile \"{}\" does not exist!\n".format(self.pidfile))
			return # not an error in a restart

		# Get the pid from the pidfile
		try:
			with open(self.pidfile,'r') as pf:
				pid = int(pf.read().strip())
		except (IOError, ValueError) as err:
			sys.stderr.write("Error: could not read pidfile \"{}\"!\n".format(self.pidfile))
			sys.exit(err)

		# Try killing the daemon process
		try:
			while 1:
				os.kill(pid, signal.SIGTERM)
				time.sleep(0.1)
		except OSError as err:
			if str(err.args).find("No such process") > 0:
				if os.path.exists(self.pidfile):
					os.remove(self.pidfile)
			else:
				sys.exit(err)

	def restart(self):
		"""Restart the daemon."""
		self.stop()
		self.start()

	def run(self):
		"""You should override this method when you subclass Daemon.

		It will be called after the process has been daemonized by
		start() or restart()."""

