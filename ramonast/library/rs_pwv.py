from library.peewee import *
import copy

# This class doesn't work, database not exposed to us
"""
class Database(Database):
	def create_view_query(self, model_class, safe, extra=''):
		framing = safe and "CREATE VIEW IF NOT EXISTS %s AS %s%s;" or "CREATE VIEW %s AS %s%s;"
		
		if extra:
			extra = ' ' + extra
		
		query = model_class._viewmeta.build_query()
		
		table = self.quote_name(model_class._meta.db_table)

		return framing % (table, query, extra)

	def create_view(self, model_class, safe=False, extra=''):
		self.execute(self.create_view_query(model_class, safe, extra))

	def drop_view(self, model_class, fail_silently=False):
		framing = fail_silently and 'DROP VIEW IF EXISTS %s;' or 'DROP VIEW %s;'
		self.execute(framing % self.quote_name(model_class._meta.db_table))
"""


# Allow the rshift syntax from the model
class ModelRshift(Model.__metaclass__):
	def __rshift__(cls, attr):
		return ViewField(cls._meta.get_field_by_name(attr))

class Model(Model):
	__metaclass__ = ModelRshift
		

# Just want to extend this a bit...
class ForeignKeyField(ForeignKeyField):
	def __rshift__(self, attr):
		# This allows the >> syntax to be chained to indicate joins
		# Return a class containing the model and the field
		
		return ViewField(self) >> attr

# This class allows joins to be indicated for views by ">>"
class ViewField:
	def __init__(self, field):
		self.field = field
		self.context = self
		self.alias = None
		self.child = None
	
	# This is a complex one. Every time this class is dotted it will search the joined
	# model for the attribute, and store it in the stack. Context always points to the
	# furthest child.
	# When these classes are "recursed" through it will start at the leftmost item in the
	# chain and pass to the right
	def __rshift__(self, attr):
		# Create the JoinedField for the new relation, look up the remote join
		self.context.child = ViewField(self.field.to._meta.get_field_by_name(attr))
		# Bump the context down a notch, pointing to the new end of the chian
		self.context = self.context.child
		return self


# The proper metaclass (BaseModel) isn't exposed, so Model.__metaclass__ is used
class BaseView(Model.__metaclass__):
	view_query = False
	def __new__(cls, name, bases, attrs):
		view_fields = []
		for attr_name, attr in attrs.iteritems():
			if(isinstance(attr,Field)):
				# Is a standard field, wrap in a ViewField
				attr = ViewField(attr)
			
			if(isinstance(attr,ViewField)):
				attr.alias = attr_name
				view_fields.append(attr)
				# The deep copy must be done for a reason, even if I don't know it?
				# Perhaps it shouldn't be copied...
				attrs[attr_name] = copy.deepcopy(attr.context.field)

		#cls.build_query(view_fields)
		
		obj = super(BaseView, cls).__new__(cls, name, bases, attrs)
		
		return obj
		
	# Can this be moved into the metaclass?
	@classmethod
	def build_query(cls,fields):
		# This will tell the select statement what to select
		selected_fields = cls.build_selection(fields)
		join_def = cls.build_join_def(fields)
		
		query = False
		for model, joins in join_def.iteritems():
			if not query:
				# The first model gets the select
				query = model.select(selected_fields)
			else:
				# Unions not implemented
				raise NotImplemented
			query = cls.perform_joins(query, model, joins)
		return query
	
	@classmethod
	def perform_joins(cls, query, model, joins):
		for join_model, join_joins in joins.iteritems():
			query = query.switch(model)
			query = query.join(join_model)
			query = cls.perform_joins(query, join_model, join_joins)

	@classmethod
	def build_selection(cls, fields):
		selection = {}
		for field in fields:
			assert(isinstance(field,ViewField))
			# This model is the furthest down on the chain, the actual one being selected
			model = field.context.field.model
			if(model not in selection):
				selection[model] = []
			selection[model].append((field.context.field.name,field.alias))
			
		return selection
	
	@classmethod
	def build_join_def(cls, fields):
		joins = {}
		for field in fields:
			current_field = field
			join_context = joins
			while True:
				model = current_field.field.model
				if(model not in join_context):
					join_context[model] = {}
				join_context = join_context[model]
				if(current_field.child != None):
					current_field = current_field.child
				else:
					break
		return joins

class View(Model):
	__metaclass__ = BaseView

	@classmethod
	def create_table(cls, fail_silently=False, extra=''):
		raise NotImplemented
	@classmethod
	def drop_table(cls, fail_silently=False):
		raise NotImplemented

	@classmethod
	def create_view(cls, fail_silently=False, extra=''):
		# TODO: figure out if table_exists covers views
		if fail_silently and cls.table_exists():
			return

        #cls._meta.database.create_table(cls, extra=extra)

	@classmethod
	def drop_view(cls, fail_silently=False):
		cls._meta.database.drop_view(cls, fail_silently)