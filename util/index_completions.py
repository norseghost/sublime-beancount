#!/usr/bin/env python3
from sys import stdin, stdout
from beancount import loader
from beancount.core.data import Transaction, Open, Close, Commodity
import pickle

def build_index(beanfile):
  entries, errors, options = loader.load_file(beanfile)

  index = {
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
      index['meta.account.beancount'].add(entry.account)
      if entry.currencies:
        index['meta.currency.beancount'].update(entry.currencies)
    elif isinstance(entry,Close) and entry.account in index['meta.account.beancount']:
      # Remove closed accounts
      index['meta.account.beancount'].remove(entry.account)
    elif isinstance(entry, Commodity):
      index['meta.currency.beancount'].add(entry.currency)
    elif isinstance(entry, Transaction):
      if entry.payee:
        index['meta.payee.beancount'].add(entry.payee)
      if entry.narration:
        index['meta.narration.beancount'].add(entry.narration)
      if entry.links:
        index['meta.link.beancount'].update(entry.links)
      if entry.tags:
        index['meta.tag.beancount'].update(entry.tags)

    meta_keys = entry.meta.keys() - ignored_keys
    if meta_keys:
      index['meta.metadata.key.beancount'].update(meta_keys)
      string_keys = set(filter(lambda k: isinstance(entry.meta[k], str), meta_keys))
      meta_values = { entry.meta[k] for k in string_keys }
      index['meta.metadata.value.beancount'].update(meta_values)
  return index, options

if __name__ == '__main__':
  output = None
  input = pickle.load(stdin.buffer)
  options_map = None

  if input['options_map_dump']:
    options_map = pickle.loads(input['options_map_dump'])

  if not options_map or loader.needs_refresh(options_map):
    index, options = build_index(input['beanfile'])
    output = {
      'index': index,
      'options_map_dump': pickle.dumps(options)
    }

  pickle.dump(output, stdout.buffer, protocol=3)
  stdout.buffer.flush()
