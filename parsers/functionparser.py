import re

from lineparser import LineParser

class FunctionData():
	"""Passed to each reviewer, as an element of the functions list, inside file_data.
	Instances of this class have the following attributes:
	- name: the name of the function
	- signature: an array of argument names
	- body: the text of the body of the function
	- lines: an instance of utils.parsers.lineparser.LineParser.LineData"""
	
	def __init__(self, name, signature, body, lines, line_nb):
		self.name = name
		self.signature = signature
		self.body = body
		self.lines = lines
		self.line_nb = line_nb
	
	def __repr__(self):
		return "Function " + self.name + ", line " + str(self.line_nb) + " (" + str(self.signature) + ") (" + str(len(self.line_data.total_lines)) + " lines of code)"

class FunctionParser:

	FUNCTIONS_PATTERNS = ["function[\s]+([a-zA-Z0-9_$]+)[\s]*\(([a-zA-Z0-9,\s]*)\)[\s]*\{",
						"([a-zA-Z0-9_$]+)[\s]*=[\s]*function[\s]*\(([a-zA-Z0-9,\s]*)\)[\s]*\{",
						"([a-zA-Z0-9_$]+)[\s]*:[\s]*function[\s]*\(([a-zA-Z0-9,\s]*)\)[\s]*\{"]
	SIGNATURE_PATTERN = "[a-zA-Z0-9_$]+"
	FUNCTIONS_BODY_PROCESSOR_SEP = "[[FUNCTIONSTART]]"
	
	def _parse_signature(self, src):
		return re.findall(FunctionParser.SIGNATURE_PATTERN, src)
		
	def _parse_bodies(self, src, pattern):
		bodies = []

		while True:
			src = re.sub(pattern, FunctionParser.FUNCTIONS_BODY_PROCESSOR_SEP, src, 1)
			split = src.split(FunctionParser.FUNCTIONS_BODY_PROCESSOR_SEP, 1)
			if len(split) > 1:
				src = split[1]
				if src[0:1] == "\n":
					src = src[1:]
				if src[-1:] == "\n":
					src = src[:-1]
				
				# Read the chars from the beginning of this function to find the end
				opened_curly_brace = 0
				body = ""
				for char in src:
					# closing the function
					if char == "}" and opened_curly_brace == 0:
						break
					# closing an already opened brace
					if char == "}" and opened_curly_brace > 0:
						opened_curly_brace -= 1
					if char == "{":
						opened_curly_brace += 1
					body += char
				
				bodies.append(body)
			else:
				break

		return bodies
	
	def parse(self, src):
		functions = []
		body_line_parser = LineParser()
		
		for pattern in FunctionParser.FUNCTIONS_PATTERNS:
			functions_bodies = self._parse_bodies(src, pattern)
			functions_signatures = re.finditer(pattern, src)
			for index, function_match in enumerate(functions_signatures):
				name = function_match.group(1)
				signature = self._parse_signature(function_match.group(2))
				body = functions_bodies[index]
				line_nb = src[0:function_match.start()].count("\n") + 1
				line_data = body_line_parser.parse(body)
				function = FunctionData(name, signature, body, line_data, line_nb)
				functions.append(function)

		return functions


if __name__ == "__main__":
	parser = FunctionParser()

	content = """/**
	 * This is a test class
	 * @param {String} test
	 */
	my.package.Class = function() {
		// This function does something
		var a = 1;

		/**
		 * some field
		 * @type {Boolean}
		 */
		this.someField = false; /* and some inline block comment */
	};

	my.package.Class.prototype = {
		/**
		 * Return the current value of the field
		 */
		getField : function() {
			// Just simply return the field
			var test = 1;
			for(var i = 0; i < 4; i++) {
				var something = test[i];
			}
			return this.someField; // And some inline comment
		}
	};
	"""

	functions = parser.parse(content)

	assert len(functions) == 2, 1
	assert functions[0].name == "Class", 2
	assert len(functions[0].line_data.all_lines) == 9, 3
	assert functions[1].name == "getField", 4
	assert len(functions[1].line_data.all_lines) == 7, 5

	content_with_inner_function = """
	test = function() {
		var a = function() {
			var b = 1;
			return b;
		}

		if(test) {
			return false;
		}

		return a;
	};"""

	functions = parser.parse(content_with_inner_function)

	assert len(functions) == 2, 6
	assert functions[0].name == "test", 7
	assert len(functions[0].line_data.all_lines) == 11, 8
	assert functions[1].name == "a", 9
	assert len(functions[1].line_data.all_lines) == 3, 10

	print "ALL TESTS OK " + __file__