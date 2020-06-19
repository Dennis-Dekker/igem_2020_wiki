module CustomHelpers
	def is_current_page(path)
		current_page.path == path ? " active" : ""
    end
end
