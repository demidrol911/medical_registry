Ext.define('MyApp.store.main.DepartmentListStore', {
	extend: 'Ext.data.Store',
	model: 'MyApp.model.main.DepartmentListModel',
	proxy: {
		type: 'ajax',
		url: '/viewer/json/department-registries/',
		timeout: 99999999,
		reader: {
			type: 'json',
			rootProperty: 'root'
		}
	},
	autoLoad: true	
})