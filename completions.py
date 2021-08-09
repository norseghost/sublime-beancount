import sublime
import sublime_plugin
import subprocess
import pickle
import re

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
        super().__init__()

    def update_index(self, view):
        # Update index if new beanfile
        view_beanfile = view.settings().get('beanfile')
        if view_beanfile != self.beanfile:
            self.beanfile = view_beanfile
            self.update_index()

        cmd = ["/usr/bin/env", "python3", "sublime-beancount/util/index_completions.py", self.beanfile]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        self.index = pickle.load(proc.stdout)
        self.index['meta.account.beancount'].update(sub_accounts(self.index['meta.account.beancount']))

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
                # print("sublime-beancount: Completion for " + k)
                # print(self.index[k])
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
    regions = view.find_by_selector("meta.amount.posting.beancount")
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
        if not len(self.view.sel()) == 1 and self.view.sel()[0].a == self.view.sel()[0].b:
            return

        loc = self.view.sel()[0].a
        if not self.view.match_selector(loc, "source.beancount & meta.amount.posting.beancount"):
            return

        region = self.view.extract_scope(loc)

        # Locate the decimal position of the region
        amount = self.view.substr(region)
        region_decimal_col = self.view.rowcol(region.a + get_decimal_offset(amount))[1]

        # Get setting
        if not self.decimal_column:
            self.decimal_column = guess_decimal_column(self.view)

        offset = self.decimal_column - region_decimal_col

        # Insert spaces
        if offset >= 0:
            self.view.insert(edit, region.a, ' ' * offset)
            return
        else:
            region.b = region.a
            region.a += offset - 1
            candidate = self.view.substr(region)
            if candidate.isspace():
                region.a += 1
                self.view.erase(edit, region)
