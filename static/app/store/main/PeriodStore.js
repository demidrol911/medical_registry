Ext.define('MyApp.store.main.PeriodStore', {
	extend: 'Ext.data.ArrayStore',
	model: 'MyApp.model.main.PeriodModel',
	alias: 'store.periods',
	storeId: 'periods',
	data: [
        ['01', "01 - Январь"],
		['02', "02 - Февраль"],	
		['03', "03 - Март"],	
		['04', "04 - Апрель"],	
		['05', "05 - Май"],	
		['06', "06 - Июнь"],	
		['07', "07 - Июль"],	
		['08', "08 - Август"],	
		['09', "09 - Сентябрь"],	
		['10', "10 - Октябрь"],	
		['11', "11 - Ноябрь"],	
		['12', "12 - Декабрь"],	
		
	],
	autoLoad: true
})