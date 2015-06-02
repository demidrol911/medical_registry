Ext.define('MyApp.model.service.AdditionalServiceInfoModel', {
    extend: 'Ext.data.Model',
    fields: [
        {name: 'disease', type: 'string'},
        {name: 'service', type: 'string'},
        {name: 'division', type: 'string'},
        {name: 'profile', type: 'string'},
		{name: 'errors', type: 'string'}
	]                    
})