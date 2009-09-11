# How many subscribers to contact at a time when delivering events.
EVENT_SUBSCRIBER_CHUNK_SIZE = 50

# Maximum number of times to attempt a subscription retry.
MAX_SUBSCRIPTION_CONFIRM_FAILURES = 4

# Period to use for exponential backoff on subscription confirm retries.
SUBSCRIPTION_RETRY_PERIOD = 30 # seconds

# Maximum number of times to attempt to pull a feed.
MAX_FEED_PULL_FAILURES = 4

# Period to use for exponential backoff on feed pulling.
FEED_PULL_RETRY_PERIOD = 30 # seconds

# Maximum number of times to attempt to deliver a feed event.
MAX_DELIVERY_FAILURES = 4

# Period to use for exponential backoff on feed event delivery.
DELIVERY_RETRY_PERIOD = 30 # seconds

# Number of polling feeds to fetch from the Datastore at a time.
BOOSTRAP_FEED_CHUNK_SIZE = 200

# Maximum age in seconds of a failed EventToDeliver before it is cleaned up.
EVENT_CLEANUP_MAX_AGE_SECONDS = (10 * 24 * 60 * 60)  # 10 days

# How many completely failed EventToDeliver instances to clean up at a time.
EVENT_CLEANUP_CHUNK_SIZE = 50

# How far before expiration to refresh subscriptions.
SUBSCRIPTION_CHECK_BUFFER_SECONDS = (24 * 60 * 60)  # 24 hours

# How many subscriber checking tasks to scheudle at a time.
SUBSCRIPTION_CHECK_CHUNK_SIZE = 200

# How often to poll feeds.
POLLING_BOOTSTRAP_PERIOD = 10800  # in seconds; 3 hours

# Default expiration time of a lease.
DEFAULT_LEASE_SECONDS = (30 * 24 * 60 * 60)  # 30 days

# Maximum expiration time of a lease.
MAX_LEASE_SECONDS = DEFAULT_LEASE_SECONDS * 3  # 90 days

# Maximum number of redirects to follow when feed fetching.
MAX_REDIRECTS = 7

# Number of times to try to split FeedEntryRecord, EventToDeliver, and
# FeedRecord entities when putting them and their size is too large.
PUT_SPLITTING_ATTEMPTS = 10

# Maximum number of FeedEntryRecord entries to look up in parallel.
MAX_FEED_ENTRY_RECORD_LOOKUPS = 500

# Maximum number of FeedEntryRecord entries to save at the same time when
# a new EventToDeliver is being written.
MAX_FEED_RECORD_SAVES = 100

# Maximum number of new FeedEntryRecords to process and insert at a time. Any
# remaining will be split into another EventToDeliver instance.
MAX_NEW_FEED_ENTRY_RECORDS = 200