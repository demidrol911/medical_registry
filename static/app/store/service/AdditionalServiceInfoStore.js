Ext.define('MyApp.store.service.AdditionalServiceInfoStore', {
	extend: 'Ext.data.Store',
	requires: ['MyApp.model.service.AdditionalServiceInfoModel'],
	model: 'MyApp.model.service.AdditionalServiceInfoModel',
	alias: 'store.additional-info',
	storeId: 'additional-info',
	proxy: {
		type: 'ajax',
		url: '/viewer/json/additional-info/',
		timeout: 200000,
		reader: {
			type: 'json',
			rootProperty: 'info'
		}
	}
})