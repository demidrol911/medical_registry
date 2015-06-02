Ext.application({
    name: 'MyApp',
	
    extend: 'MyApp.Application',
	appFolder: '/static/app/',
	
	stores: ['MyApp.store.main.YearStore', 'MyApp.store.main.PeriodStore', 'MyApp.store.main.RegistryListStore', 
	'MyApp.store.main.DepartmentListStore', 'MyApp.store.main.RegistryStatusStore', 
	'MyApp.store.service.OrganizationServiceStore', 'MyApp.store.service.OrganizationEventStore',
	'MyApp.store.service.AdditionalServiceInfoStore', 'MyApp.store.service.ServiceTermStore',
	'MyApp.store.service.ServiceDivisionStore', 'MyApp.store.service.ServiceProfileStore', 'MyApp.store.service.ServiceProfileArrayStore'],
	
    autoCreateViewport: 'MyApp.view.main.Main'

});