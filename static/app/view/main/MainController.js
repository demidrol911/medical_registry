Ext.define('MyApp.view.main.MainController', {
    extend: 'Ext.app.ViewController',

    alias: 'controller.main',

	requires: ['MyApp.view.main.PeriodWindow', 'MyApp.view.service.ServiceWindow'],
	
	getOrganizationGrid: function() {
		return this.lookupReference('OrganizationRegistryGrid')
	},
	
	getDepartmentGrid: function() {
		return this.lookupReference('DepartmentRegistryGrid')
	},

	getOrganizationStore: function() {
		return this.getOrganizationGrid().getStore();
	},
	
	getDepartmentStore: function() {
		return this.getDepartmentGrid().getStore();
	},
	
    onSelectPeriodClick: function () {
		var view = this.getView();
		this.selectPeriodDialog = view.add({xtype: 'period-window'});
		this.selectPeriodDialog.show();
    },
	
	onRegistryListChange: function(field, newVal, oldVal) {
		this.enableButtons();
	},
	
	onSaveRegistryList: function() {
		var organizationStore = this.getOrganizationStore();
		var departmentStore = this.getDepartmentStore();
		
		organizationStore.sync();
		organizationStore.commitChanges();

		departmentStore.sync();
		departmentStore.commitChanges();

		this.disableButtons();
		
	},

	onCancelRegistryList: function() {
		var organizationStore = this.getOrganizationStore();
		var departmentStore = this.getDepartmentStore();
		
		organizationStore.rejectChanges();
		departmentStore.rejectChanges();	
		
		this.disableButtons();
	},
	
	disableButtons: function() {
		Ext.getCmp('btnCancelRegistryList').disable();
		Ext.getCmp('btnAcceptRegistryList').disable();
	},
	
	enableButtons: function() {
		Ext.getCmp('btnCancelRegistryList').enable();
		Ext.getCmp('btnAcceptRegistryList').enable();	
	},
	
	onDepartmentFastFilter: function () {
		var organizationGrid = this.getOrganizationGrid();
		var organizationStore = this.getOrganizationStore();
		var departmentStore = this.getDepartmentStore();		
	
		if (organizationGrid.getSelectionModel().hasSelection()) {
		    var row = organizationGrid.getSelectionModel().getSelection()[0];
		    console.log(row.get('organization_code'));
		   
  		    if (!departmentStore.isLoading()) {
				this.lookupReference('RegistryTabPanel').setActiveTab(1);
				var department = row.get('organization_code');
				
				departmentStore.filter('organization_code', department);
		    } else {
				Ext.MessageBox.show({
					title: 'Ой!',
					msg: 'Список подразделений ещё не загрузился, подождите немного.',
					buttons: Ext.MessageBox.OK
				})
			}
		}	
	},
	
	onResetFastFilter: function () {
		var departmentStore = this.getDepartmentStore();		
		var organizationStore = this.getOrganizationStore();
		
		if (!organizationStore.isLoading()) {
			organizationStore.clearFilter()
		}
		
		if (!departmentStore.isLoading()) {
			departmentStore.clearFilter()
		}
	},
	
	onOrganizationListKeyDown: function(view, record, item, index, key) {
		if (key.getKey() == 115) {
			this.onDepartmentFastFilter();
		}
	},
	
	onOrganizationListDblClick: function(view, record, item, index) {
		var view = this.getView();
		var data = record.data;
		var viewmodel = this.getViewModel();
		
		this.serviceWindow = view.add({
			xtype: 'service-window', 
		});
		
		viewmodel.setData({
			organizationListRecord: data,
			advancedSearchFormData: {}
		})

		viewmodel.setStores({
			additionalInfo: {type: 'additional-info'},
			services: {type: 'organization-services'},
		})
		
		this.serviceWindow.show();		
	},
	
	onDepartmentListDblClick: function(view, record, item, index) {
		var view = this.getView();	
		var data = record.data;
		var viewmodel = this.getViewModel();
		
		this.serviceWindow = view.add({
			xtype: 'service-window', 
		});
		
		viewmodel.setData({
			organizationListRecord: data,
			advancedSearchFormData: {}
		})

		viewmodel.setStores({
			additionalInfo: {type: 'additional-info'},
			//services: {type: 'organization-services'},
		})
		
		this.serviceWindow.show();		
	},	
	
});