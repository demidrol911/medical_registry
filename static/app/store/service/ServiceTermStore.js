Ext.define('MyApp.store.service.ServiceTermStore', {
	extend: 'Ext.data.ArrayStore',
	requires: ['MyApp.model.service.ServiceTermModel'],
	model: 'MyApp.model.service.ServiceTermModel',
	alias: 'store.service-term',
	storeId: 'service-term',
	
	data: [
		[1, 'Стационар'],
		[2, 'Дневной стационар'],
		[3, 'Поликлиника'],
		[4, 'Скорая помощь']
	]
})