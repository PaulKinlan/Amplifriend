import hubmodel
from SubscribeHandler import SubscribeHandler
from SubscriptionConfirmHandler import SubscriptionConfirmHandler
from SubscriptionReconfirmHandler import SubscriptionReconfirmHandler

import constants
import logging 

DEBUG = True

if DEBUG:
  logging.getLogger().setLevel(logging.DEBUG)



def utf8encoded(data):
  """Encodes a string as utf-8 data and returns an ascii string.

  Args:
    data: The string data to encode.

  Returns:
    An ascii string, or None if the 'data' parameter was None.
  """
  if data is None:
    return None
  return unicode(data).encode('utf-8')


def unicode_to_iri(url):
  """Converts a URL containing unicode characters to an IRI.

  Args:
    url: Unicode string containing a URL with unicode characters.

  Returns:
    A properly encoded IRI (see RFC 3987).
  """
  scheme, rest = unicode(url).encode('utf-8').split(':', 1)
  return '%s:%s' % (scheme, urllib.quote(rest))


def sha1_hash(value):
  """Returns the sha1 hash of the supplied value."""
  return hashlib.sha1(utf8encoded(value)).hexdigest()


def get_hash_key_name(value):
  """Returns a valid entity key_name that's a hash of the supplied value."""
  return 'hash_' + sha1_hash(value)


def sha1_hmac(secret, data):
  """Returns the sha1 hmac for a chunk of data and a secret."""
  return hmac.new(secret, data, hashlib.sha1).hexdigest()


def is_dev_env():
  """Returns True if we're running in the development environment."""
  return 'Dev' in os.environ.get('SERVER_SOFTWARE', '')


def work_queue_only(func):
  """Decorator that only allows a request if from cron job, task, or an admin.

  Also allows access if running in development server environment.

  Args:
    func: A webapp.RequestHandler method.

  Returns:
    Function that will return a 401 error if not from an authorized source.
  """
  def decorated(myself, *args, **kwargs):
    if ('X-AppEngine-Cron' in myself.request.headers or
        'X-AppEngine-TaskName' in myself.request.headers or
        is_dev_env() or users.is_current_user_admin()):
      return func(myself, *args, **kwargs)
    elif users.get_current_user() is None:
      myself.redirect(users.create_login_url(myself.request.url))
    else:
      myself.response.set_status(401)
      myself.response.out.write('Handler only accessible for work queues')
  return decorated


def is_valid_url(url):
  """Returns True if the URL is valid, False otherwise."""
  split = urlparse.urlparse(url)
  if not split.scheme in ('http', 'https'):
    logging.debug('URL scheme is invalid: %s', url)
    return False

  netloc, port = (split.netloc.split(':', 1) + [''])[:2]
  if port and not is_dev_env() and port not in VALID_PORTS:
    logging.debug('URL port is invalid: %s', url)
    return False

  if split.fragment:
    logging.debug('URL includes fragment: %s', url)
    return False

  return True


_VALID_CHARS = (
  'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
  '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '_',
)


def get_random_challenge():
  """Returns a string containing a random challenge token."""
  return ''.join(random.choice(_VALID_CHARS) for i in xrange(128))