import sublime, sublime_plugin, re, json
from os.path import dirname, split, exists, join, realpath



def sortLines(lines, config):
	def getSortKey(line):
		keyword = re.split(r'[\(\s:]+', line.lstrip())[0]
		return config.index(keyword) if keyword in config else len(config)
	return sorted(lines, key=getSortKey)



def getRightSelection(sel, view):
	while view.substr(sel)[-1] != '\n' and sel.end() < view.size():
		sel = sublime.Region(sel.begin(), sel.end() + 1)

	while view.substr(sel)[0] != '\n' and sel.begin() > 0:
		sel = sublime.Region(sel.begin() - 1, sel.end())

	return sublime.Region(sel.begin() + 1, sel.end() - 1)



def findStylintrc(path):
	path = dirname(path)
	count = 0
	while path != realpath('/'):
		stylintrcPath = join(path, '.stylintrc')
		if (exists(stylintrcPath)):
			return stylintrcPath
		path = realpath(join(path, '..'))
	print('.stylintrc not found. Using default config')
	return join(dirname(__file__), '.stylintrc')



commentRe = re.compile(
	'(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
	re.DOTALL | re.MULTILINE
)

def parseJson(filename):
	with open(filename) as f:
		content = ''.join(f.readlines())

		## Looking for comments
		match = commentRe.search(content)
		while match:
			# single line comment
			content = content[:match.start()] + content[match.end():]
			match = commentRe.search(content)

		return json.loads(content)



def getConfig(path):
	stylintrcPath = findStylintrc(path)
	data = parseJson(stylintrcPath)
	return data['sortOrder']



class StylintSortingCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		config = getConfig(self.view.file_name())
		view = self.view
		for sel in [s for s in view.sel() if not s.empty()]:
			sel = getRightSelection(sel, view)
			lines = [b for b in view.substr(sel).split('\n') if b]

			firstIndent = len(lines[0]) - len(lines[0].lstrip())
			for line in lines[1:]:
				thisLineIndent = len(line) - len(line.lstrip())
				if (firstIndent != thisLineIndent):
					raise Exception('different indent')

			view.replace(edit, sel, '\n'.join(sortLines(lines, config)))
