Ext.define('MyApp.view.main.PeriodWindowController', {
    extend: 'Ext.app.ViewController',

    alias: 'controller.periodwindow',

	onConfirmPeriodClick: function () {
		var mainView = Ext.getCmp('MainView');
		var organizationGrid = mainView.lookupReference('OrganizationRegistryGrid');
		var departmentGrid = mainView.lookupReference('DepartmentRegistryGrid');
		var importGrid = mainView.lookupReference('ImportGrid');
		var organizationStore = organizationGrid.getStore();
		var departmentStore = departmentGrid.getStore();
		var registryImportStore = importGrid.getStore();
		var model = this.getViewModel();

		organizationStore.reload({params: {'year': model.data.year, 'period': model.data.period}});
		departmentStore.reload({params: {'year': model.data.year, 'period': model.data.period}});
		registryImportStore.reload({params: {'year': model.data.year, 'period': model.data.period}});		
		
		this.view.destroy();
	},
	
	onClose: function (panel, opts) {
		panel.remove(this, true);
	}

	
});