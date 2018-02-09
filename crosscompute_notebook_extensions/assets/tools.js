var notebook;

define([
  'base/js/namespace',
  'base/js/dialog'
], function(jupyter, dialog) {

  var $modal;
  var $toolbar = $('#maintoolbar-container');
	var keyboard_manager = jupyter.keyboard_manager;
	notebook = jupyter.notebook;

  function backup_notebook() {

    show_modal('Starting backup...', 'Please be patient.');
    notebook.events.one('notebook_saved.Notebook', function() {
      $.ajax({
        method: 'post',
        url: notebook.base_url + 'extensions/crosscompute/backup.json',
        data: {'_xsrf': get_cookie('_xsrf')}
      }).fail(function(jqXHR) {
        switch(jqXHR.status) {
          case 501:
            show_modal('Notebook backup available only on website', '<p>Notebook backup only works on the <a href="https://crosscompute.com" target="_blank">CrossCompute Website</a>.</p>');
            break;
          case 503:
            show_modal('Notebook backup failed', '<p>This service is temporarily unavailable. Please try again in a few minutes.</p>');
            break;
        }
      }).done(function(d) {
        show_modal('Notebook backup succeeded', '<p><a href="X" target="_blank">Click here to see your notebook</a>.</p>'.replace('X', d.notebook_url));
      });
    });
    notebook.save_notebook();

  }

  function preview_tool() {
    process_notebook('preview', 'preview');
  }

  function deploy_tool() {
    if (notebook.notebook_name == 'Untitled.ipynb') {
      return show_modal('Tool name required', 'Your notebook is Untitled. Please give a name to your notebook. The name of the notebook will become the name of the tool.');
    }
    process_notebook('deploy', 'deployment');
  }

  function process_notebook(verb, noun) {
    function render_text(x) {
      return x.replace(/X/g, noun);
    }

		var code_cell = notebook.container.find('.code_cell').first().data('cell');
		if (code_cell === undefined || !/crosscompute/i.test(code_cell.get_text())) {
      show_modal(render_text('Tool X cancelled'), '<p>This notebook does not appear to be a CrossCompute Tool.</p><p><a href="https://crosscompute.com/create#create-tools" target="_blank">Please make sure the first code cell contains the word CrossCompute</a>.</p>');
      return;
    }

    show_modal(render_text('Preparing tool X...'), 'Please be patient.');
    notebook.events.one('notebook_saved.Notebook', function() {
      $.ajax({
        method: 'post',
        url: notebook.base_url + 'extensions/crosscompute/X.json'.replace(/X/g, verb),
        data: {
          '_xsrf': get_cookie('_xsrf'),
          'notebook_path': notebook.notebook_path
        }
      }).fail(function(jqXHR) {
        switch(jqXHR.status) {
          case 400:
            var d = jqXHR.responseJSON;
            show_modal(render_text('Tool X failed'), d.text ? '<pre>' + d.text + '</pre>' : 'Unable to reach server.');
            break;
          case 401:
            show_modal('Server token required', '<textarea class="form-control"></textarea>');
            var $textarea = $modal.find('textarea');
            $modal.one('hidden.bs.modal', function() {
              var server_token = $.trim($textarea.val());
              if (!server_token.length) return;
              update_configuration('server_token', server_token);
            });
            break;
          case 403:
            show_modal('Account sign-in required', 'Anonymous sessions cannot X tools. <a href="https://crosscompute.com" target="_blank">Please sign in and start a new session</a> to X this tool.'.replace(/X/g, verb));
            break;
        }
      }).done(function(d) {
        var body = '<p><a href="X" target="_blank">Click here to access your tool</a>.</p>'.replace(/X/g, d.tool_url);
        if (verb == 'preview') {
          body += '<p>Note that your tool preview will stop working after the notebook session ends. Deploy the tool using the Red Button to make it available on <a href="https://crosscompute.com" target="_blank">CrossCompute</a>.</p>';
        } else if (verb == 'deploy') {
          body += '<p>Its visibility is <b>hidden</b>, which means that only users with the exact url will be able to access the tool. You can choose to make the tool public by clicking the eye icon at the top of the deployed tool. If you make it public, the tool will appear on your profile.</p>';
        }
        show_modal(render_text('Tool X succeeded'), body);
      });
    });
    notebook.save_notebook();
    setTimeout(function() {
      if ($('.modal').length > 1) {
        $modal.modal('hide');
      }
    }, 500);
  }

  function update_configuration(variable_name, variable_value) {
    $.ajax({
      method: 'post',
      url: notebook.base_url + 'extensions/crosscompute/configure.json',
      data: {
        '_xsrf': get_cookie('_xsrf'),
        'variable_name': variable_name,
        'variable_value': variable_value,
      },
      success: function(d) {
        show_modal('Configuration update succeeded', 'Please retry your request.');
      },
      error: function(jqXHR) {
        show_modal('Configuration update failed', 'Could not update configuration at this time.');
      }
    });
  }

  function get_cookie(name) {
    var r = document.cookie.match('\\b' + name + '=([^;]*)\\b');
    return r ? r[1] : undefined;
  }

  function show_modal(title, body) {
    if (!$modal) {
      $modal = dialog.modal({
        notebook: notebook,
        keyboard_manager: keyboard_manager,
        buttons: {'Close': {}}
      });
    }
    $modal.find('.modal-title').text(title);
    $modal.find('.modal-body').html(body);
    $modal.modal('show');
  }

  function set_toolbar_button_css(action_name, d) {
    var x = 'button[data-jupyter-action="X"]';
    $toolbar.find(x.replace('X', action_name)).css(d);
  }

  function load_ipython_extension() {
    var actions = keyboard_manager.actions;
    var shortcuts = keyboard_manager.command_shortcuts;

    var backup_notebook_action_name = actions.register({
      'icon': 'fa-paper-plane-o',
      'help': 'backup notebook',
      'help_index': 'crosscompute-backup',
      'handler': backup_notebook
    }, 'notebook-backup', 'crosscompute');
    var preview_tool_action_name = actions.register({
      'icon': 'fa-paper-plane-o',
      'help': 'preview tool',
      'help_index': 'crosscompute-preview',
      'handler': preview_tool
    }, 'tool-preview', 'crosscompute');
    var deploy_tool_action_name = actions.register({
      'icon': 'fa-paper-plane-o',
      'help': 'deploy tool',
      'help_index': 'crosscompute-deploy',
      'handler': deploy_tool
    }, 'tool-deploy', 'crosscompute');

    shortcuts.add_shortcut('Shift-C,Shift-P', preview_tool_action_name);
    shortcuts.add_shortcut('Shift-C,Shift-D', deploy_tool_action_name);

    jupyter.toolbar.add_buttons_group([
      backup_notebook_action_name,
      preview_tool_action_name,
      deploy_tool_action_name
    ]);

    set_toolbar_button_css(preview_tool_action_name, {'background-color': '#286090', 'color': '#e6e6e6'});
    set_toolbar_button_css(deploy_tool_action_name, {'background-color': '#d9534f', 'color': '#e6e6e6'});
  }

  return {
    load_ipython_extension: load_ipython_extension
  };

});
