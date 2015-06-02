Ext.define('MyApp.model.service.OrganizationEventModel', {
    extend: 'Ext.data.Model',
    fields: [
        {name: 'first_name', type: 'string'},
        {name: 'last_name', type: 'string'},
        {name: 'middle_name', type: 'string'},
        {name: 'birthdate', type: 'date', dateReadFormat: 'Y-m-d'},
        {name: 'gender', type: 'string'},
        {name: 'policy', type: 'string'},
        {name: 'wrk_code', type: 'string'},
        {name: 'anamnesis', type: 'string'},
		{name: 'uet', type: 'float'},
        {name: 'event_id', type: 'int'},
		{name: 'evt_comment', type: 'string'},
		{name: 'initial_disease', type: 'string'},
		{name: 'basic_disease', type: 'string'},
		{name: 'complicated_disease', type: 'string'},
		{name: 'concomitant_disease', type: 'string'},
		
    ]                    
})