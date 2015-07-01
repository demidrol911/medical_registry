Ext.define('MyApp.view.service.AdvancedSearchWindowController', {
    extend: 'Ext.app.ViewController',

    alias: 'controller.advanced-search-window-controller',
	
	compare: function (a,b) {
		if (a[0] < b[0]) return -1;
		if (a[0] > b[0]) return 1;
		return 0;
	},
	

	onAdvancedSearchRun: function () {
		console.log('Ok!');
		var view = this.getView();
		var model = this.getViewModel();
		var modelData = model.data;
		var formView = this.lookupReference('advanced-search-form');
		var form = formView.getForm();
		
		if (form.isValid()) {
			var store = modelData.services;
			store.clearFilter();
			
			var fieldValues = form.getFieldValues();
			model.setData({advancedSearchFormData: fieldValues});			
			
			if (fieldValues.policy) {
				store.filter('policy', fieldValues.policy);
			}
			
			if (fieldValues.last_name) {
				store.filter('last_name', fieldValues.last_name);
			}
			
			if (fieldValues.first_name) {
				store.filter('first_name', fieldValues.first_name);
			}

			if (fieldValues.middle_name) {
				store.filter('middle_name', fieldValues.middle_name);
			}
			
			if (fieldValues.birthdate) {
				store.filter('birthdate', fieldValues.birthdate);
			}
			
			if (fieldValues.term) {
				store.filter('term', fieldValues.term);
			}
			
			if (fieldValues.disease_1 && fieldValues.disease_2) {
				store.filterBy(function (record, id) {
					disease = record.get('disease_code');
					if (disease >= fieldValues.disease_1 && disease <= fieldValues.disease_2) {return true} 
					return false
				})
			} else if (fieldValues.disease_1) {
				store.filter('disease_code', fieldValues.disease_1);
			}

			if (fieldValues.service_1 && fieldValues.service_2) {
				store.filterBy(function (record, id) {
					service = record.get('service_code');
					if (service >= fieldValues.service_1 && service <= fieldValues.service_2) {return true} 
					return false
				})
			} else if (fieldValues.service_1) {
				var matchingArray = fieldValues.service_1.match(/[0-9]{6}/g);
				
				if (matchingArray) {
					if (matchingArray.length == 1) {
						store.filter('service_code', fieldValues.service_1);
					} else if (matchingArray.length > 1) {
						store.filterBy(function (record, id) {
							service = record.get('service_code');
							
							var is_matching = false;	
							for (var i = 0; i < matchingArray.length; i++) {
								if (service == matchingArray[i]) {is_matching = true;}
							}
							if (is_matching) {return true}
						})
					}
				}
			}

			if (fieldValues.start_date_1 && fieldValues.start_date_2) {
				store.filterBy(function (record, id) {
					start_date = record.get('start_date');
					if (start_date >= fieldValues.start_date_1 && start_date <= fieldValues.start_date_2) {return true} 
					return false
				})
			} else if (fieldValues.start_date_1) {
				store.filter('start_date', fieldValues.start_date_1);
			}

			if (fieldValues.end_date_1 && fieldValues.end_date_2) {
				store.filterBy(function (record, id) {
					end_date = record.get('end_date');
					if (end_date >= fieldValues.end_date_1 && end_date <= fieldValues.end_date_2) {return true} 
					return false
				})
			} else if (fieldValues.end_date_1) {
				store.filter('end_date', fieldValues.end_date_1);
			}
			
			if (fieldValues.division) {
				var arr = fieldValues.division.split(',');
				var divisionCode = arr[0].trim();
			
				store.filter('division_code', divisionCode);
			}
			
			if (fieldValues.profile) {
				store.filter('profile_name', fieldValues.profile);			
			}
			
		} else {console.log('Form is not valid');}

		view.destroy();
	},
	
	onAfterRender: function (me, otps) {
		var form = this.lookupReference('advanced-search-form');
		console.log('Start');
		var model = this.getViewModel();
		var modelData = model.data;
		form.getForm().setValues(modelData.advancedSearchFormData);
		console.log('alert');
		var keyNav = new Ext.util.KeyNav({
			target: 'advancedSearchWindow',
			enter: {
				fn: function(e) {
					console.log('Form submit');
					this.onAdvancedSearchRun();
				},
				defaultEventAction: 'stopEvent'
			},
			scope: this
		}); 			
	},
	
	onProfileComboboxRender: function (me, opts) {
		var model = this.getViewModel();
		var modelData = model.data;
		var profile_data = model.data.services.collect('profile_name', false, true);
		me.store.loadData(profile_data.map(function(name) {return [name]}));
	},

	onDivisionComboboxRender: function (me, opts) {
		var model = this.getViewModel();
		var modelData = model.data;
		var divisionsData = []
		var divisionRec = []
		
		model.data.services.each(function(rec) {
			divisionRec = [rec.get('division_code'), rec.get('division_name')]
			
			if (divisionsData.length == 0) {divisionsData.push(divisionRec)}
			var exists = false;
			for (var i = 0; i < divisionsData.length; i++) {
				if (divisionsData[i][0] == divisionRec[0]) {
					exists = true;
					break;
				}
			}
			
			if (!exists && divisionRec[0].length > 1) {
				divisionsData.push(divisionRec);
			}

		});
		
		console.log(divisionsData.length);
		divisionsData = divisionsData.sort(this.compare);

		me.store.loadData(divisionsData.map(function(name) {return [name]}));
	},
	/*
	onFormAfterRender: function(me) {
		var form = this.lookupReference('advanced-search-form');
		console.log(form.id);
		
		var keyNav = new Ext.util.KeyNav({
			target: form.id,
			enter: {
				fn: function(e) {
					console.log('Form submit');
					me.onAdvancedSearchRun();
				}
			},
			scope: this
		}); 	
	}*/
});