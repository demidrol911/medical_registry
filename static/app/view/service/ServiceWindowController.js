Ext.define('MyApp.view.service.ServiceWindowController', {
    extend: 'Ext.app.ViewController',

    alias: 'controller.servicewindow',
	
	timer: false,
	
	onAfterRenderWindow: function(me, opts) {
		var model = this.getViewModel();
		var mydata = model.data;
		
		if (mydata.organizationListRecord.department_code) {
			me.setBind({
		title: 'Реестр {organizationListRecord.organization_name}, подразделение {organizationListRecord.department_code}, период: {organizationListRecord.year}-{organizationListRecord.period}'
	})
		}
	
	},
		
	onAfterRenderGrid: function () {
		var view = this.getView();
		var eventGrid = this.lookupReference('event-grid');
		eventGrid.store.removeAll();
		
		grid = this.lookupReference('service-grid');
		grid.setLoading('Загружаются услуги. Подождите...');
		var model = this.getViewModel();
		var mydata = model.data;
		
		model.data.services.load({
			params: {
				year: mydata.organizationListRecord.year,
				period: mydata.organizationListRecord.period, 
				organization: mydata.organizationListRecord.organization_code,
				department: mydata.organizationListRecord.department_code
			},
			callback: function (records, operation, success) {
				grid.setLoading(false);
				grid.down('#status').update({count: records.length});
			}
		});
		
		
	},
	
	onServiceGridSelectionChange: function (me, records) {
		if (records.length) {

			var record = records[0];
			var eventGrid = this.lookupReference('event-grid');
			var grid = this.lookupReference('service-grid');
			
			eventGrid.store.loadRecords(records);

			var additionalInfoView = this.lookupReference('additional-info-form');
			var additionalInfoForm = additionalInfoView.getForm();

			if (this.timer) {
				clearTimeout(this.timer);
			}
			this.timer = setTimeout(function () {
				additionalInfoForm.loadRecord(record);
			}, 60);

		}
	},
	onRender: function (me, options) {
		
	},
	
	onAdvancedSearchClick: function () {
		var view = this.getView();
		this.advancedSearchDialog = view.add({xtype: 'advanced-search-service-window'});
		this.advancedSearchDialog.show();	
	},
	
	onAdvancedSearchReset: function () {
		var grid = this.lookupReference('service-grid');		
		var store = grid.getStore();
		store.clearFilter();
		grid.filters.clearFilters();
		console.log('---- after clear filters ----');
		console.log(grid.filters);
		var model = this.getViewModel();
		var mydata = model.data;		
		mydata.advancedSearchFormData = {};
		
	},
	
	onExportToExcel: function () {
		var grid = this.lookupReference('service-grid');
		var model = this.getViewModel();
		var mydata = model.data;		
		var filters = grid.store.getFilters();
		
		console.log('---- before export filters ----');
		console.log(filters)
		
		var params = {};
		var params = mydata.advancedSearchFormData;
		console.log('advanced search form data');
		console.log(mydata.advancedSearchFormData);
		console.log('params from form');
		console.log(params);		
		params['year'] = mydata.organizationListRecord.year;
		params['period'] = mydata.organizationListRecord.period;
		params['organization_code'] = mydata.organizationListRecord.organization_code;
		params['department_code'] = mydata.organizationListRecord.department_code;
		
		for (var i = 0;  i < filters.items.length; i ++) {
			if (!params.hasOwnProperty(filters.items[i]._property)) {
				if (filters.items[i]._value instanceof Array) {
					params[filters.items[i]._property] = filters.items[i]._value.join();
				} else {
					params[filters.items[i]._property] = filters.items[i]._value;
				}
			} 
		}
		console.log('params after for cycle');
		console.log(params);
		var view = this.getView();
		view.mask('Загружается акт...');

		Ext.Ajax.request({
			url: '/viewer/excel-export/',
			method: 'POST',
			timeout: 9999999,
			scope: this,
			params: params,
			success: function(response, opts) {
				view.unmask('Загружается акт...');

				var disposition = response.getResponseHeader('Content-Disposition');
				var filename = disposition.slice(disposition.indexOf("=")+1,disposition.length);
				
				var a = document.createElement("a");				
				a.href = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,'+ response.responseText
				a.download = filename;
				document.body.appendChild(a);
				a.click();
				a.remove();
			},
			failure: function() {
				view.unmask('Загружается акт...');
			}
		});

		
	},
	
	'onFilterChange': function(store, filters, opts) {
		console.log('filter changed');
		var grid = this.lookupReference('service-grid');
		grid.removeClsWithUI('stripe-second-row');
	}
});