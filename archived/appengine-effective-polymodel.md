---
title: Effective PolyModel on App Engine Standard Environment
description: Learn how to build effective polymodels on Google App Engine standard environment.
author: devlance
tags: App Engine, Datastore
date_published: 2009-08-01
---

*Rafe Kaplan*

*August 2009*

The world is a complex place and it's sometimes hard to pigeon-hole ideas in to
a single representational model. When writing software one would ideally like to
account for variations in different categories of objects, but still be able to
treat them as a single basic type. Many developers these days are used to using
polymorphic class hierarchies to achieve this. App Engine provides a simple way
to create polymorphic class hierarchies that can still be queried as a single
kind. This article will describe how to use this method and some useful things
you can do with it.

## A catalog of types

Andreas is an enterprising fellow who is about to start his own online shop that
sells an assortment of consumer electronics ranging from digital cameras to
video players to computers.  He wants to make it possible for visitors to his
site to search the various products on relevant properties common to all items
such as price and brand, but also let them narrow their search to more specific
categories using properties specific to those items.

A simple way to model the catalog using the basic App Engine Model would be to
place all the fields needed for each product in a single class and have a field
indicating its type in order to determine which fields are needed.

```py
class CatalogItem(db.Model):
    name = db.StringProperty()
    brand = db.StringProperty()
    price = db.FloatProperty(required=True)
    category = db.StringProperty(
        choices=['camera', 'video', 'computer'])

    # Camera Properties
    ram = db.IntegerProperty()
    megapixels = db.IntegerProperty()
    memory_type = db.StringProperty(choices=['pocketmem',
                                             'datarod',
                                             'fastchip'])

    # Video Player Properties
    disk_trays = db.IntegerProperty()
    output_hdmi = db.BooleanProperty()
    output_component = db.BooleanProperty()
    output_svideo = db.BooleanProperty()

    # Computer Properties
    ghz = db.FloatProperty()
    # NOTE: The ram property is shared between camera and laptop.
    hard_drive = db.IntegerProperty()
```

With AJAX, it's not that hard for Andreas to write forms that are customized
based on what the customer is looking for. GQL also makes it easy to do the
search.  For example, if a customer is looking for a new 8 megapixel camera the
query would probably look like:

    CatalogItem.gql("WHERE category='camera' AND megapixels=8")

There's a few problems with this model the way it is. At a very low level it's
hard to determine what properties should be used for a given catalog category.
Calling the properties method on a given CatalogItem instance will retrieve all
properties for all categories. If Andreas wanted to use reflection to show him
the properties of his catalog in the Google Cloud Console, he would see all the
properties for that item whether it uses it or not. Another problem is the fact
that cameras and computers share the same field, but it might have different
meanings. For example, camera RAM might be measured in megabytes, whereas
computer memory in gigabytes. They're not really the same property.

## Meet polyModel

Instead of placing all products in to a single class, it is possible to define
each category as its own class that fits naturally in to a product category
hierarchy. To do this, create a subclass of PolyModel instead of Model. Let's
see how Andreas redesigns the basic product model:

```py
from google.appengine.ext import db
from google.appengine.ext.db import polymodel

class CatalogItem(polymodel.PolyModel):
    name = db.StringProperty()
    brand = db.StringProperty()
    price = db.FloatProperty(required=True)

    @property
    def category(self):
        return self.class_name().lower()


class Camera(CatalogItem):
    megapixels = db.IntegerProperty()
    ram = db.IntegerProperty(
        validator=lambda ram: ram >= 128 and ram <= 2048)
    memory_type = db.StringProperty(choices=['pocketmem',
                                             'datarod',
                                             'fastchip'])


class Video(CatalogItem):
    disk_trays = db.IntegerProperty()
    output_hdmi = db.BooleanProperty()
    output_component = db.BooleanProperty()
    output_svideo = db.BooleanProperty()


class Computer(CatalogItem):
    ghz = db.FloatProperty()
    ram = db.FloatProperty(
        validator=lambda ram: ram >= 1.0 and ram <= 8.0)
    hard_drive = db.IntegerProperty()
```

There are a few things to notice about the new class definitions. For one, there
is no longer a need to explicitly set the products category. This can be
calculated automatically (if needed) by calling class_name() on a PolyModel
instance. But since it is not a persistant property, how does one query for
products of a particular category?  How this is done is one of the most powerful
and important features of PolyModel.  Using `all()` or `gql()` on a PolyModel
class will perform a query over all instances of that class and all instances of
all of its sub-classes.  This feature of PolyModel is called
"polymorphic queries". So for example, this queries all Computers that run at or
over 2.0 GHz:

```py
Computer.gql('WHERE ghz > 2.0')
```

Another thing to notice is that each category is independently responsible for
maintaining its own properties. Recall that originally that the Computer
category and the Camera category had to share the same ram property. Now,
Camera.ram and Computer.ram are completely different properties on different
classes and therefore can have completely different definitions that even have
different constraints, as illustrated. The other way to have done this in the
non-polymorphic model would have been to give each ram property its own name,
like computer_ram and camera_ram. As the model grows, there are more potential
property name conflicts that can pop up. In this respect, using a polymorphic
class can act as a little name space for different categories of your model.

## Creating a polymorphic property

Andreas is bright and innovative and has some ideas that he can add to his
online store to distinguish himself from his competitors. With so many products
with so many features it can be very difficult for people to decide which
product is the best, or which ones are of good value. To help the customer
choose which he wants to add an automatically calculated "Quality Rating" field
based on the number and sophistication of features on an item and a secret
mathematical formula of his own devising.

The problem here is that how the calculation is done depends on the type of
object in the catalog. For example, he needs to calculate the Quality Rating of
a camera based on the megapixels and the supported memory types, video players
on the kinds of outputs it has and number of disk trays, and computers on speed,
memory and storage capacity. "Fortunately", Andreas  thinks, "computer science
has provided us with a special tool for just this kind of situation!" Andreas
is of course thinking of the `if` statement:

```py
class CatalogItem(db.Model):
    # ...

    quality_rating = db.FloatProperty()

    def set_quality_rating(self):
        self.quality_rating = self.calculate_quality_rating()

    def calculate_quality_rating(self):
        raise NotImplementedError(
            'Need to define this for each category')


class Camera(CatalogItem):
    # ...

    def calculate_quality_rating(self):
        memory_type_score = {
            'pocketmem': 1.3,
            'datarod': 1.0,
            'fastchip': 0.9
        }[self.memory_type]
        return self.megapixels * memory_type_score + self.ram


class Video(CatalogItem):
    # ...

    def calculate_quality_rating(self):
        output_hdmi_score = 0.0
        output_component_score = 0.0
        output_svideo_score = 0.0
        if self.output_hdmi: output_hdmi_score = 3.0
        if self.output_component: output_component_score = 2.0
        if self.output_video: output_svideo_score = 1.0
        features = (output_hdmi_score +
                    output_component_score +
                    output_svideo_score)
        return self.disk_trays * features

class Computer(CatalogItem):
    # ...

    def calculate_quality_rating(self):
        return self.ghz * self.ram + self.hard_drive
```

And thus, Andreas goes out and builds his new website. But there's something
worth noting here.

## Further refinements

Very soon, as he looks over his proposed inventory, it becomes apparent to
Andreas that he needs to continue to narrow the searches over the products he
has. For example, he sells two kinds of computers, desktops and laptops. When
shopping for laptops, suddenly the computers weight and battery life becomes
very important. He could just add a weight and battery life to the computer
category, but most folks don't usually care how much a desktop weighs, and
battery life is altogether meaningless!  Furthermore, most people come looking
specifically for a desktop or a laptop, so it would make sense to separate
desktops and laptops in to their own categories. On the other hand, some
customers might very well have not chosen which kind of computer they want and
would like to compare the relative merits between desktops and laptops. Placing
desktops and laptops in to separate categories means they forget their original
association as a related category. Andreas should be able to write a kind of GQL
query that would allow someone to search on both category types. Is there a way?

There is.

## Sub-categories done right

Now that Andreas has created a class hierarchy for his online store, he can
easily implement sub-categories for laptops and desktops:

```py
class Desktop(Computer):

    slots = db.IntegerProperty()

    def calculate_quality_rating():
        rating = super(Desktop, self).calculate_quality_rating()
        return  rating * self.slots

class Laptop(Computer):

    weight = db.FloatProperty()

    def calculate_quality_rating():
        rating = super(Laptop, self).calculate_quality_rating()
        return rating / self.weight

# Let's create an example catalog of computers.
Laptop( name='The Superlight', weight=3.4, ram=1.0).put()
Laptop( name='Robusto',        weight=8.9, ram=2.0).put()
Desktop(name='Workstation D',  slots=2,    ram=2.0).put()
Desktop(name='Workhorse',      slots=8,    ram=8.0).put()
```

When the user wants to search for laptops that are a certain weight or less, all
the application needs to do is:

    >>> selected_weight = 5.0
    ... for laptop in Laptop.gql('WHERE weight <= :1', selected_weight):
    ...  print laptop.name

    The Superlight

This query will only return laptops.

If the user wants to search for desktop computers with a minimum number of slots
the application would do:

    >>> minimum_slots = 4
    ... for desktop in Desktop.gql('WHERE slot >= :1', minimum_slots):
    ...  print desktop.name

    Workhorse

If the user is wants to see all computers that have a certain amount of memory
or more, all the application needs to do is:

    >>> selected_ram = 2.0
    ... for computer in Computer.gql('WHERE ram >= :1', selected_ram):
    ...   print computer.name

    Robusto
    Workstation D
    Workhorse

This will query all computers, laptop and desktop alike. However, it is very
easy to narrow this same query to *just* laptops:

    >>> for laptop in Laptop.gql('WHERE ram >= :1', selected_ram):
    ...  print laptop.name

    Robusto

Using polymorphic queries allows an intuitive way to query over objects of
different types that share a similar basic purpose, but allow those objects to
maintain their specific structure.

## Why this works

It might help to understand a little bit about how this polymorphism is
implemented. All sub-classes of a given class hierarchy root share the same
Google Cloud Datastore kind. To differentiate between classes within the
hierarchy, the PolyModel has an extra hidden string list property, class, in the
Cloud Datastore. This list, known as the class key, describes that particular
object's location in the class hierarchy. Each element of this list is the name
of a class, starting with the root of the hierarchy at index 0. Because queries
against a list match if any elements match the query value, searching for an
object using the name of one class will match the class keys of all instances
that contain that class name.

For the online shop models, the class keys for each class look like this:

    CatalogItem: ['CatalogItem'                             ]
    Camera:      ['CatalogItem',  'Camera'                  ]
    Computer:    ['CatalogItem', 'Computer'                 ]
    Desktop:     ['CatalogItem', 'Computer',  'Desktop'     ]
    Laptop:      ['CatalogItem', 'Computer',  'Laptop'      ]

When a call to `Computer.gql` or `Computer.all` is made an equality query is
made against the class property for the class name (as defined by
`PolyModel.class_name()`). If Andreas was working in the Cloud Console and
wanted to hand write a query for all computers that 4 GB or more of RAM, he can
write:

    SELECT * FROM CatalogItem WHERE class = 'Laptop' and ram >= 4.0

In practice, however, outside of applications such as the Cloud Console, the
class property should never be used directly. The name of the class should
always be accessed using `PolyModel.class_name()` and the class key by
`PolyModel.class_key()`. Avoid calling `db.gql` directly in production code,
always using the gql class method associated with the class you would like to
query.

## Things to watch out for

It might be tempting to make every single class in an application a PolyModel
class, even for classes that do not immediately require a subclass. However it
should not normally be required to create a PolyModel class earlier so that it
might be subclassed in the future. If the application sticks to using the class
method version of gql and all it is future compatible to change the inheritance
from Model to PolyModel later. This is because calls to gql and all on the
class hierarchy root class do not attempt to query against class property.

But why not make everything a PolyModel anyway?  There is not too much of a
problem making everything a PolyModel, except that each instance must be stored
with its class information. This value is pretty small and in practice may not
cause a problem, but it is something to consider.

Also be careful not to create large class hierarchies of unrelated object types.
For example, it's not wise to attempt to create a single polymorphic root class
that every class in the application inherits from. The main reason not to do
this is that it ensures every query in your application will require a composite
index. For an application with a lot of data, this could end up taking up a lot
of space disk space with these indexes for queries that give no real benefit.

## Conclusion

The introduction of polymorphic queries to App Engine creates a very intuitive
way to create collections of similar but variable Cloud Datastore types. It
makes it easier to design models using standard object oriented techniques and
access them according to their taxonomy. PolyModel cannot be used for
everything, but with care, more complicated models can be easier to maintain and
extend.
