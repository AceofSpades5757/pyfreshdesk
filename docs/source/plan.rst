Freshdesk Plan
==============

.. code:: python
  from freshdesk import Client
  from freshdesk import Plan


  fd = Client(
      domain='mydomain',
      api_key='MY_API_KEY',
      plan=Plan.ESTATE,
  )
