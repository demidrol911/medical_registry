Ext.define('MyApp.model.serviceModel', {
    extend: 'Ext.data.Model',
    fields: [
        {name: 'id', type: 'int'},
        {name: 'first_name', type: 'string'},
        {name: 'last_name', type: 'string'},
        {name: 'middle_name', type: 'string'},
        {name: 'birthdate', type: 'string'},
        {name: 'gender', type: 'string'},
        {name: 'policy', type: 'string'},
        {name: 'end_date', type: 'string'},
        {name: 'division_code', type: 'string'},
        {name: 'division_name', type: 'string'},
        {name: 'service_code', type: 'string'},    
        {name: 'service_name', type: 'string'},
        {name: 'quantity', type: 'int'},
        {name: 'disease_code', type: 'string'},
        {name: 'accepted_payment', type: 'float'},
        {name: 'worker_code', type: 'string'},
        {name: 'anamnesis_number', type: 'string'},
        {name: 'event_id', type: 'int'},
        {name: 'errors', type: 'string'},
        {name: 'full_name', type: 'string'}
    ]                    
})