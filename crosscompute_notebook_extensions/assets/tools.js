define([
  'base/js/namespace',
  'base/js/dialog',
], function(jupyter, dialog) {

  function preview_tool() {
    var notebook = jupyter.notebook;
    var notebook_path = notebook.notebook_path;
    var base_url = notebook.base_url;

    var feedback_dialog = dialog.modal({
      notebook: notebook,
      keyboard_manager: notebook.keyboard_manager,
      title: 'Preparing tool preview...',
      body: 'Please be patient.'
    });

    notebook.save_notebook();
    notebook.events.one('notebook_saved.Notebook', function () {
      $.ajax({
        url: base_url + 'crosscompute/preview.json',
        data: {
          'notebook_path': notebook_path
        },
        success: function(d) {
          feedback_dialog.modal('hide');
          open(d.tool_url, '_blank');
        },
        error: function(jqXHR) {
          var d = jqXHR.responseJSON;
          feedback_dialog.find('.modal-title').text('Tool preview failed');
          feedback_dialog.find('.modal-body').text(d.text);
        }
      });
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

    var $toolbar = $('#maintoolbar-container');
    $toolbar.find('button[data-jupyter-action="' + preview_tool_action_name + '"]').css('background-color', '#5cb85c');
  }

  return {
    load_ipython_extension: load_ipython_extension
  };
});
