Ext.define('MyApp.store.main.YearStore', {
	extend: 'Ext.data.ArrayStore',
	requires: ['MyApp.model.main.YearModel'],
	model: 'MyApp.model.main.YearModel',
	alias: 'store.years',
	storeId: 'years',
	data: [
        ['2015', "2015"],
        ['2014', "2014"],
        ['2013', "2013"]		
	],
	autoLoad: true
})