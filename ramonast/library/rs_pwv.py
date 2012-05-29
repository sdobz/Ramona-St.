from library.peewee import *
import copy

# This class doesn't work, database not exposed to us
"""
class Database(Database):
	def drop_view(self, model_class, fail_silently=False):
"""


# Allow the rshift syntax from the model
class ModelRshift(Model.__metaclass__):
	def __rshift__(cls, other):
		model = None
		if(isinstance(other,ForeignKeyField)):
			# The field name is an extra bit of informtion not typically needed
			field_name = other.name
			model = other.model
		elif(isinstance(other, Model)):
			model = other
			field_name = None

		if(model):
			# Chain together the field and the reverse lookup
			reverse_field = cls._meta.get_reverse_related_field_for_model(model, field_name)
			return ViewField(cls) + ViewField(reverse_field)
		
		# Otherwise just look up the field as a string
		return ViewField(cls._meta.get_field_by_name(other))

class Model(Model):
	__metaclass__ = ModelRshift

# If the >> syntax is used on a foreign key first convert it to a ViewField
class ForeignKeyField(ForeignKeyField):
	def __rshift__(self, other):
		return ViewField(self) >> other

class ViewField:
	def __init__(self, field_or_model):
		if(isinstance(field_or_model,Field)):
			self.chain = [field_or_model.model]
			self.field = field_or_model
		else:
			self.chain = [field_or_model]
			self.field = None
		self.alias = None

	def name(self):
		return self.field.name
	def model(self):
		return self.field.model

	# Search the rightmost model for the attribute, and add it to the stack.
	def __rshift__(self, other):
		assert isinstance(other,basestring), "Can only shift by strings"
		assert isinstance(self.field,ForeignKeyField), "Can only shift if %s is foreign key" % self.name()
		# Look up the field "other" in the foreign model
		return self + ViewField(self.field.to._meta.get_field_by_name(other))

	def __lshift__(self, other):
		self.field = self.model()._meta.get_field_by_name(other)
		return self

	# The add command adds the object onto the end of the chain
	def __add__(self, other):
		self.chain.append(other.model())
		self.field = other.field
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
				attrs[attr_name] = copy.deepcopy(attr.field)
		
		obj = super(BaseView, cls).__new__(cls, name, bases, attrs)
		
		obj._meta.view_query = cls.build_query(view_fields)

		return obj
	
	@classmethod
	def build_query(cls,fields):
		query = False
		for model, joins in cls.build_joins(fields).iteritems():
			if not query:
				# The first model gets the select
				query = model.select(cls.build_selection(fields))
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
		return query

	@classmethod
	def build_selection(cls, fields):
		# The select query should be able to handle a generator,
		# but instead a dict must be passed
		selection = {}
		for field in fields:
			# Remember field is a ViewField instance
			# This model is the model of the rightmost field
			model = field.model()
			# Each model must have it's own list
			if(model not in selection):
				selection[model] = []
			
			selection[model].append((field.name(),field.alias))
			
		return selection
	
	@classmethod
	def build_joins(cls, fields):
		joins = {}
		# In effect this merges all of the chains of models
		for field in fields:
			join_context = joins
			for model in field.chain:
				if(model not in join_context):
					# If the model isn't at the current join level add it
					join_context[model] = {}
				# Traverse a level deeper
				join_context = join_context[model]

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
	def view_query(cls):
		return cls._meta.view_query

	@classmethod
	def drop_view(cls, fail_silently=False):
		#cls._meta.database.drop_view(cls, fail_silently)
		framing = fail_silently and 'DROP VIEW IF EXISTS %s;' or 'DROP VIEW %s;'
		cls._meta.database.execute(framing % self.quote_name(cls._meta.db_table))
	
	@classmethod
	def create_view_query(cls, model_class, safe, extra=''):
		framing = safe and "CREATE VIEW IF NOT EXISTS %s AS %s%s;" or "CREATE VIEW %s AS %s%s;"
		
		if extra:
			extra = ' ' + extra
		
		query = model_class.view_query().sql()
		
		table = model_class._meta.database.quote_name(model_class._meta.db_table)

		return framing % (table, query, extra)
	
	@classmethod
	def create_view(self, safe=False, extra=''):
		model_class = self
		database = self._meta.database
		database.execute(self.create_view_query(model_class, safe, extra))


		
