define([
	'base/js/namespace',
], function(jupyter) {

  function preview_tool() {
    var notebook = jupyter.notebook;
    var notebook_path = notebook.notebook_path;
    var base_url = notebook.base_url;

    $.post(base_url + 'crosscompute/preview', {
      'notebook_path': notebook_path
    }, function() {
    });

  }

  function load_ipython_extension() {
    var keyboard_manager = jupyter.keyboard_manager;

    var actions = keyboard_manager.actions;
    var shortcuts = keyboard_manager.command_shortcuts;

    var preview_tool_action_name = actions.register({
      'icon': 'fa-paper-plane-o',
      'help': 'preview tool',
      'help_index': 'crosscompute-preview',
      'handler': preview_tool
    }, 'preview-tool', 'crosscompute');
    shortcuts.add_shortcut('Shift-C,Shift-P', preview_tool_action_name);

    jupyter.toolbar.add_buttons_group([
      preview_tool_action_name,
    ]);
	}

	return {
		load_ipython_extension: load_ipython_extension
	};
});
