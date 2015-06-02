Ext.define('MyApp.store.service.ServiceProfileArrayStore', {
	extend: 'Ext.data.ArrayStore',
	storeId: 'service-array-profile',
	fields: ['profile'],
	sorters: 'profile'
})