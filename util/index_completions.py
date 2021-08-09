#!/usr/bin/env python3
from sys import argv, stdout
from beancount import loader
from beancount.core.data import Transaction, Open, Close, Commodity
import pickle

entries, errors, options = loader.load_file(argv[1])

output = {
  'meta.account.beancount': set(),
  'meta.payee.beancount': set(),
  'meta.narration.beancount': set(),
  'meta.link.beancount': set(),
  'meta.tag.beancount': set(),
  'meta.currency.beancount': set(),
  'meta.metadata.key.beancount': set(),
  'meta.metadata.value.beancount': set()
}

ignored_keys = { 'filename', 'lineno', '__tolerances__' }

for entry in entries:

  if isinstance(entry, Open):
    output['meta.account.beancount'].add(entry.account)
    if entry.currencies:
      output['meta.currency.beancount'].update(entry.currencies)
  elif isinstance(entry, Commodity):
    output['meta.currency.beancount'].add(entry.currency)
  elif isinstance(entry, Transaction):
    if entry.payee:
      output['meta.payee.beancount'].add(entry.payee)
    if entry.narration:
      output['meta.narration.beancount'].add(entry.narration)
    if entry.links:
      output['meta.link.beancount'].update(entry.links)
    if entry.tags:
      output['meta.tag.beancount'].update(entry.tags)

  meta_keys = entry.meta.keys() - ignored_keys
  if meta_keys:
    output['meta.metadata.key.beancount'].update(meta_keys)
    string_keys = set(filter(lambda k: isinstance(entry.meta[k], str), meta_keys))
    meta_values = { entry.meta[k] for k in string_keys }
    output['meta.metadata.value.beancount'].update(meta_values)

pickle.dump(output, stdout.buffer, protocol=3)

