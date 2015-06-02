Ext.define('MyApp.view.service.ServiceViewModel', {
	extend: 'Ext.app.ViewModel',
	alias: 'viewmodel.service-viewmodel',
	
	formulas: {
		record_year: function () {return this.getView().gridData.year}, // почему-то свойство с именем year не объявляется в объекте
		record_period: function () {return this.getView().gridData.period},
		record_organization_code: function () {return this.getView().gridData.code},
		organization_name: function () {return this.getView().gridData.name}
	},

	stores: {
		services: {
			type: 'organization-services', 
		}
	}

})

