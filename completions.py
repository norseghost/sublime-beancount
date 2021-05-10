import sublime
import sublime_plugin
import subprocess
import pickle

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

    def guess_decimal_column(self, view):
        regions = view.find_by_selector("meta.amount.beancount")
        for r in regions:
            print(view.substr(r))

    def on_query_context(self, view, key, operator, operand, match_all):
        if view.syntax().scope != "source.beancount":
            return

        # self.guess_decimal_column(view)
        return False

