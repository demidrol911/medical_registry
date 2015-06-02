Ext.define('MyApp.model.main.DepartmentListModel', {
	extend: 'Ext.data.Model',
	fields: [
		{name: 'department_code', type: 'string'},
		{name: 'department_name', type: 'string'},
		{name: 'year', type: 'string'},
		{name: 'period', type: 'string'},
		{name: 'department_status', type: 'string'},
		{name: 'department_timestamp', type: 'date', dateReadFormat: 'd-m-Y'},
		{name: 'organization_code', type: 'string'},
		{name: 'organization_name', type: 'string'},
	]
})
