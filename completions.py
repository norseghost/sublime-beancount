import sublime
import sublime_plugin
import subprocess
import pickle
import re
import time

def sans_root(account_name):
    components = account_name.split(':')[1:]
    return ':'.join(components)

def sub_accounts(x):
    output = set()
    if len(x):
        output = { sans_root(account_name) for account_name in x if sans_root(account_name) }
        output.update(sub_accounts(output))

    return output

class BeancountCompletions(sublime_plugin.EventListener):
    def __init__(self):
        self.beanfile = None
        self.index = None
        self.options_map_dump = None
        super().__init__()

    def update_index(self, view):
        # Update index if new beanfile
        self.beanfile = view.settings().get('beanfile')

        if not self.beanfile:
            return

        if view.settings().get('beancount_debug'):
            print("sublime-beancount: Updating index")

        input = {
            'beanfile': self.beanfile,
            'options_map_dump': self.options_map_dump
        }
        index_completions =sublime.packages_path() + "/sublime-beancount/util/index_completions.py"
        cmd = ["/usr/bin/env", "python3", index_completions, self.beanfile]        # cmd = ["/usr/bin/env", "pwd"]
        # print(cmd)
        proc = subprocess.run(cmd, input=pickle.dumps(input), capture_output = True)
        # print(proc.returncode)
        # print(proc.stderr)
        # print(proc.stdout)
        # return
        output = pickle.loads(proc.stdout)

        if output:
            self.index = output['index']
            self.options_map_dump = output['options_map_dump']
            self.index['meta.account.beancount'].update(sub_accounts(self.index['meta.account.beancount']))

        if view.settings().get('beancount_debug'):
            print("sublime-beancount: Updated index")

        return

    def on_load_async(self, view):
        if not view.settings().has('beanfile'):
            return
        self.update_index(view)
        return

    def on_post_save_async(self, view):
        if not view.settings().has('beanfile'):
            return
        self.update_index(view)
        return

    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(locations[0], "source.beancount"):
            return []

        if not self.index:
            self.update_index(view)

        prefix = prefix.lower()
        out = []

        # Use context of preceding word
        if view.classify(locations[0]) & sublime.CLASS_WORD_END != 0:
            locations[0] -= 1

        for k in self.index.keys():
            if view.match_selector(locations[0], k):
                if view.settings().get('beancount_debug'):
                    print("sublime-beancount: Getting completions for " + prefix + " in " + k)
                if len(prefix):
                    for comp in self.index[k]:
                        if comp.lower().startswith(prefix):
                            out.append(comp)
                else:
                    out.append(self.index[k])

        return out

def get_decimal_offset(str):
    m = re.search(r'[0-9](?=[.\s])', str)
    if not m:
        return None
    return m.start() + 1

def guess_decimal_column(view):
    regions = view.find_by_selector("source.beancount & (meta.amount.beancount - meta.metadata.value.beancount)")
    decimal_col = 0
    n = 0
    for r in regions:
        amount = view.substr(r)
        offset = get_decimal_offset(amount)
        if not offset:
            continue        
        decimal_col = (decimal_col * n + view.rowcol(r.a + offset)[1]) / (n + 1)
        n = n + 1
    return int(decimal_col)

class BeancountAlignDecimalCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        self.decimal_column = None
        super().__init__(view)

    def run(self, edit):
        for region in self.view.sel():
            if not region.empty():
                continue
            loc = region.begin()
            if not self.view.match_selector(loc, "source.beancount & (meta.amount.beancount - meta.metadata.value.beancount)"):
                continue

            scope_region = self.view.extract_scope(loc)

            # Locate the decimal position of the region
            amount = self.view.substr(scope_region)
            region_decimal_col = self.view.rowcol(scope_region.a + get_decimal_offset(amount))[1]

            # Get setting
            self.decimal_column = self.view.settings().get('beancount_decimal_column')
            if not self.decimal_column:
                self.decimal_column = guess_decimal_column(self.view)

            offset = self.decimal_column - region_decimal_col

            # Insert spaces
            if offset >= 0:
                self.view.insert(edit, scope_region.a, ' ' * offset)
                return
            else:
                scope_region.b = scope_region.a
                scope_region.a += offset - 1
                candidate = self.view.substr(scope_region)
                if candidate.isspace():
                    scope_region.a += 1
                    self.view.erase(edit, scope_region)

class BeancountInsertDateCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for s in view.sel():
            if s.empty():
                view.insert(edit, s.a, time.strftime('%Y-%m-%d'))
            else:
                view.replace(edit, s, time.strftime('%Y-%m-%d'))

