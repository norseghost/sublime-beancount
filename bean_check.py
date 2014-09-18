import sublime, sublime_plugin, subprocess, os

class BeanCheckCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        print("Running!")
        self.run_check(edit)

    def show_report_buffer(self, report, text, edit):
        report_buffer = self.view.window().new_file()
        report_buffer.set_scratch(True)
        report_buffer.set_syntax_file("Packages/Beancount/beancount.tmLanguage")
        report_buffer.set_name("Report: %s" % report)
        report_buffer.insert(edit, 0, text)

    def show_report_panel(self, text, edit):
        output_view = self.view.window().get_output_panel("tests")
        self.view.window().run_command("show_panel", {"panel": "output.tests"})
        output_view.insert(edit, 0, text)

    def run_check(self, edit):
        #check   = subprocess.Popen([ "bean-check", filename ], universal_newlines=True, stderr=subprocess.STDOUT, stdout=subprocess.STDOUT)
        check   = subprocess.check_output([ "bean-check", self.view.file_name() ], universal_newlines=True, stderr=subprocess.STDOUT)
        #output, errors = check.communicate()
        if len(check) == 0:
            self.show_report_panel("No errors were found!", edit)
        else:
            self.show_report_panel(check, edit)
