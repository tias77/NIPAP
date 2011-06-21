#!/usr/bin/python
# vim: et :

import logging
import unittest
import sys
sys.path.append('../napd/')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_format = "%(levelname)-8s %(message)s"

import nap


class NapTest(unittest.TestCase):
    """ Tests the NAP class
    """

    logger = logging.getLogger()
    nap = nap.Nap()



    def setUp(self):
        """ Better start from a clean slate!
        """
        self.nap._execute("DELETE FROM ip_net_plan")
        self.nap._execute("DELETE FROM ip_net_pool")
        self.nap._execute("DELETE FROM ip_net_schema")

        self.schema_attrs = {
                'name': 'test-schema1',
                'description': 'Test schema numero uno!'
                }
        self.schema_attrs['id'] = self.nap.add_schema(self.schema_attrs)
        self.schema_attrs2 = {
                'name': 'test-schema2',
                'description': 'Test schema numero dos!'
                }
        self.schema_attrs2['id'] = self.nap.add_schema(self.schema_attrs2)
        self.pool_attrs = {
                'name': 'test-pool1',
                'description': 'Test pool numero uno!',
                'default_type': 'assignment',
                'ipv4_default_prefix_length': 30,
                'ipv6_default_prefix_length': 112
                }
        self.pool_attrs['id'] = self.nap.add_pool({'id': self.schema_attrs['id']}, self.pool_attrs)
        self.prefix_attrs = {
                'authoritative_source': 'naptest',
                'prefix': '1.3.3.1/32',
                'description': 'Test prefix numero uno!'
                }
        self.prefix_attrs['id'] = self.nap.add_prefix({'id': self.schema_attrs['id']}, self.prefix_attrs)
        self.prefix_attrs2 = {
                'authoritative_source': 'naptest',
                'prefix': '1.3.3.0/24',
                'description': ''
                }
        self.prefix_attrs2['id'] = self.nap.add_prefix({'id': self.schema_attrs['id']}, self.prefix_attrs2)
        self.prefix_attrs3 = {
                'authoritative_source': 'naptest',
                'prefix': '1.3.0.0/16',
                'description': ''
                }
        self.prefix_attrs3['id'] = self.nap.add_prefix({'id': self.schema_attrs['id']}, self.prefix_attrs3)



    def test_schema_basic(self):
        """ Basic schema test

            1. Add a new schema
            2. List with filters to get newly created schema
            3. Verify listed schema coincides with input args for added schema
            4. Remove schema
        """
        attrs = {
                'name': 'test-schema-wrong',
                'description': 'A simple test schema with incorrect name!'
                }
        attrs['id'] = self.nap.add_schema(attrs)
        schema = self.nap.list_schema({ 'id': attrs['id'] })
        for a in attrs:
            self.assertEqual(schema[0][a], attrs[a], 'Added object differ from listed on attribute: ' + a)



    def test_schema_add_crap_input(self):
        """ Try to input junk into add_schema and expect error

        """
        attrs = {
                'name': 'test-schema-crap',
                'description': 'A simple test schema with incorrect name!',
                'crap': 'this is just some crap'
                }
        # missing everything
        self.assertRaises(nap.NapMissingInputError, self.nap.add_schema, { })
        # missing description
        self.assertRaises(nap.NapMissingInputError, self.nap.add_schema, { 'name': 'crapson' })
        # have required and extra crap
        self.assertRaises(nap.NapExtraneousInputError, self.nap.add_schema, attrs)



    def test_expand_schema_spec(self):
        """ Test the expand_schema_spec()

            The _expand_schema_spec() function is used throughout the schema
            functions to expand the schema specification input and so we test
            the separately.
        """
        # wrong type
        self.assertRaises(nap.NapInputError, self.nap._expand_schema_spec, 'string')
        # wrong type
        self.assertRaises(nap.NapInputError, self.nap._expand_schema_spec, 1)
        # wrong type
        self.assertRaises(nap.NapInputError, self.nap._expand_schema_spec, [])
        # missing keys
        self.assertRaises(nap.NapMissingInputError, self.nap._expand_schema_spec, { })
        # crap key
        self.assertRaises(nap.NapExtraneousInputError, self.nap._expand_schema_spec, { 'crap': self.schema_attrs['name'] })
        # required keys and extra crap
        self.assertRaises(nap.NapExtraneousInputError, self.nap._expand_schema_spec, { 'name': self.schema_attrs['name'], 'crap': 'crap' })
        # proper key but incorrect value (int vs string)
        self.assertRaises(nap.NapValueError, self.nap._expand_schema_spec, { 'id': '3' })
        # proper key but incorrect value (int vs string)
        self.assertRaises(nap.NapValueError, self.nap._expand_schema_spec, { 'name': 3 })
        # both id and name
        self.assertRaises(nap.NapExtraneousInputError, self.nap._expand_schema_spec, { 'id': 3, 'name': '3' })
        # proper key - id
        where, params = self.nap._expand_schema_spec({ 'id': 3 })
        self.assertEqual(where, 'id = %(spec_id)s', "Improperly expanded WHERE clause")
        self.assertEqual(params, {'spec_id': 3}, "Improperly expanded params dict")
        # proper spec - name
        where, params = self.nap._expand_schema_spec({ 'name': 'test' })



    def test_schema_edit_crap_input(self):
        """ Try to input junk into edit_schema and expect error

        """
        attrs = {
                'name': 'test-schema-crap',
                'description': 'A simple test schema with incorrect name!'
                }
        crap_attrs = {
                'name': 'test-schema-crap',
                'description': 'A simple test schema with incorrect name!',
                'crap': 'this is just some crap'
                }
        # spec is tested elsewhere, just test attrs part
        self.assertRaises(nap.NapExtraneousInputError, self.nap.edit_schema, { 'name': self.schema_attrs['name'] }, crap_attrs)



    def test_schema_list_crap_input(self):
        """ Try to input junk into list_schema and expect error

        """
        # TODO: what do we really expect?
        self.assertRaises(nap.NapExtraneousInputError, self.nap.list_schema, { 'crap': 'crap crap' })



    def test_schema_dupe(self):
        """ Check so we can't create duplicate schemas

            There are unique indices in the database that should prevent us
            from creating duplicate schema (ie, with the same name).
        """
        schema_attrs = {
                'name': 'test-schema-dupe',
                'description': 'Testing dupe'
                }
        # TODO: this should raise a better exception, something like non-unique or duplicate
        self.nap.add_schema(schema_attrs)
        self.assertRaises(nap.NapError, self.nap.add_schema, schema_attrs)



    def test_schema_rename(self):
        """ Rename a schema

            Uses the edit_schema() functionality to rename our previously
            created and incorrectly named schema so it hereafter has the
            correct name. Also tests the list_schema() functionality since we
            use that to list the modified schema.
        """
        spec = { 'name': 'test-schema1' }
        attrs = {
                'name': 'test-schema',
                'description': 'A simple test schema with correct name!'
                }
        self.nap.edit_schema(spec, attrs)
        # check that search for old record doesn't return anything
        schema = self.nap.list_schema(spec)
        self.assertEqual(schema, [], 'Old entry still exists')
        schema = self.nap.list_schema({ 'name': 'test-schema' })
        for a in attrs:
            self.assertEqual(schema[0][a], attrs[a], 'Modified schema differ from listed on attribute: ' + a)



    def test_schema_remove(self):
        """ Remove a schema

            Remove the schema previously modified and make sure it's not there.
        """
        spec = { 'name': 'test-schema' }
        self.nap.remove_schema(spec)
        # check that search for old record doesn't return anything
        schema = self.nap.list_schema(spec)
        self.assertEqual(schema, [], 'Old entry still exists')



    def test_expand_pool_spec(self):
        """ Test the function which expands pool spec to SQL.
        """

        schema = {'id': self.schema_attrs['id']}

        # wrong type
        self.assertRaises(nap.NapInputError, self.nap._expand_pool_spec, 'string')
        # wrong type
        self.assertRaises(nap.NapInputError, self.nap._expand_pool_spec, 1)
        # wrong type
        self.assertRaises(nap.NapInputError, self.nap._expand_pool_spec, [])
        # missing keys
        self.assertRaises(nap.NapMissingInputError, self.nap._expand_pool_spec, { })
        # crap key
        self.assertRaises(nap.NapExtraneousInputError, self.nap._expand_pool_spec, { 'crap': self.pool_attrs['name'] })
        # required keys and extra crap
        self.assertRaises(nap.NapExtraneousInputError, self.nap._expand_pool_spec, { 'id': self.pool_attrs['id'], 'schema': self.schema_attrs['id'], 'crap': 'crap' })
        # proper key but incorrect value (int vs string)
        self.assertRaises(nap.NapValueError, self.nap._expand_pool_spec, { 'id': '3', 'schema': self.schema_attrs['id'] })
        # proper key but incorrect value (int vs string)
        self.assertRaises(nap.NapValueError, self.nap._expand_pool_spec, { 'name': 3, 'schema': self.schema_attrs['id'] })
        # both id and name
        self.assertRaises(nap.NapExtraneousInputError, self.nap._expand_pool_spec, { 'id': 3, 'name': '3', 'schema': self.schema_attrs['id'] })
        # proper key - id
        where, params = self.nap._expand_pool_spec({ 'id': 3, 'schema': self.schema_attrs['id'] })
        self.assertEqual(where, 'po.id = %(spec_id)s AND po.schema = %(spec_schema)s', "Improperly expanded WHERE clause")
        self.assertEqual(params, {'spec_id': 3, 'spec_schema': self.schema_attrs['id']}, "Improperly expanded params dict")
        # proper spec - name
        where, params = self.nap._expand_pool_spec({ 'name': 'test', 'schema': self.schema_attrs['id'] })
        self.assertEqual(where, 'po.name = %(spec_name)s AND po.schema = %(spec_schema)s', "Improperly expanded WHERE clause")
        self.assertEqual(params, {'spec_name': 'test', 'spec_schema': self.schema_attrs['id'] }, "Improperly expanded params dict")



    def test_pool_add1(self):
        """ Add a pool and check it's there using list functions

            Refer to schema by id
        """
        attrs = {
                'name': 'test-pool-wrong',
                'description': 'A simple test pool with incorrect name!',
                'default_type': 'reservation',
                'ipv4_default_prefix_length': 30,
                'ipv6_default_prefix_length': 112
                }
        schema = {'id': self.schema_attrs['id']}
        pool_id = self.nap.add_pool(schema, attrs)
        pool = self.nap.list_pool(schema, { 'id': pool_id })
        for a in attrs:
            self.assertEqual(pool[0][a], attrs[a], 'Added object differ from listed on attribute: %s  %s!=%s' % (a, attrs[a], pool[0][a]))



    def test_pool_add2(self):
        """ Add a pool and check it's there using list functions

            Refer to schema by name
        """
        schema = {'id': self.schema_attrs['id']}
        attrs = {
                'name': 'test-pool-wrong',
                'default_type': 'reservation',
                'description': 'A simple test pool with incorrect name!'
                }
        pool_id = self.nap.add_pool(schema, attrs)
        pool = self.nap.list_pool(schema, { 'id': pool_id })
        for a in attrs:
            self.assertEqual(pool[0][a], attrs[a], 'Added object differ from listed on attribute: ' + a)



    def test_edit_pool_by_name(self):
        """ Try to rename a pool using edit_pool() function

            Pool is not uniquely identified (empty spec) so this should raise an error
        """
        schema = {'id': self.schema_attrs['id']}
        spec = {  }
        attrs = {
                'name': self.pool_attrs['name'],
                'default_type': 'assignment',
                'description': 'A simple test pool with correct name!'
                }
        self.assertRaises(nap.NapInputError, self.nap.edit_pool, schema, spec, attrs)



    def test_edit_pool(self):
        """ Rename a pool using edit_pool() function
        """
        schema = {'id': self.schema_attrs['id']}
        spec = { 'id': self.pool_attrs['id'] }
        attrs = {
                'name': 'test-pool',
                'default_type': 'assignment',
                'description': 'A simple test pool with correct name!',
                'ipv4_default_prefix_length': 32,
                'ipv6_default_prefix_length': 128
                }
        self.nap.edit_pool(schema, spec, attrs)
        # check that search for old record doesn't return anything
        pool = self.nap.list_pool(schema, { 'name': self.pool_attrs['name'] })
        self.assertEqual(pool, [], 'Old entry still exists')
        pool = self.nap.list_pool(schema, { 'name': attrs['name'] })
        for a in attrs:
            self.assertEqual(pool[0][a], attrs[a], 'Added object differ from listed on attribute: ' + a)



    def test_remove_pool_by_id(self):
        """ Remove a pool by id
        """
        schema = {'id': self.schema_attrs['id']}
        pool = self.nap.list_pool(schema, { 'id': self.pool_attrs['id'] })
        # first make sure our pool exists
        self.assertNotEqual(pool[0], [], 'Record must exist before we can delete it')
        for a in self.pool_attrs:
            self.assertEqual(pool[0][a], self.pool_attrs[a], 'Listed attribute differ from original')
        # remove the pool
        self.nap.remove_pool(schema, { 'id': self.pool_attrs['id'] })
        # check that search for old record doesn't return anything
        pool = self.nap.list_pool(schema, { 'id': self.pool_attrs['id'] })
        self.assertEqual(pool, [], 'Old entry still exists')



    def test_prefix_in_a_pool(self):
        """ Add prefixes to a poll and list!
        """
        schema = {'id': self.schema_attrs['id']}
        pool = self.nap.list_pool(schema, { 'id': self.pool_attrs['id'] })
        # first make sure our pool exists
        self.assertNotEqual(pool[0], [], 'Pool must exist!')
        pfxs = [
                '1.2.2.0/32',
                '1.2.2.1/32',
                '1.2.2.2/32',
                '1.2.2.3/32',
                '1.2.2.4/32',
                '1.2.2.5/32'
                ]
        for p in pfxs:
            prefix_attrs = {
                    'authoritative_source': 'nap-test',
                    'prefix': p,
                    'description': 'test prefix',
                    'pool_id': self.pool_attrs['id'],
                    'comment': 'test comment, please remove! ;)'
                    }
            self.nap.add_prefix(schema, prefix_attrs)

        # list again
        pool = self.nap.list_pool(schema, { 'id': self.pool_attrs['id'] })
        self.assertNotEqual(pool[0], [], 'Pool must exist!')
        self.assertEqual(set(pfxs), set(pool[0]['prefixes']), 'Returned prefixes do not match added ones')



    def test_prefix_basic(self):
        """ Test basic prefix functions
        """
        schema = {'id': self.schema_attrs['id']}
        prefix_attrs = {
                'authoritative_source': 'nap-test',
                'prefix': '1.3.3.7/32',
                'description': 'test prefix',
                'comment': 'test comment, please remove! ;)'
                }
        self.nap.add_prefix(schema, prefix_attrs)
        prefix = self.nap.list_prefix(schema, { 'prefix': prefix_attrs['prefix'] })
        for a in prefix_attrs:
            self.assertEqual(prefix[0][a], prefix_attrs[a], 'Added object differ from listed on attribute: ' + a)

        # fetch many prefixes - all in a schema
        prefix = self.nap.list_prefix(schema, {})
        self.assertGreater(len(prefix), 0, 'Found 0 prefixes in schema ' + self.schema_attrs['name'])



    def test_add_prefix(self):
        """ Test add_prefix in a bit more detail
        """
        schema = {'id': self.schema_attrs['id']}
        # we need a bloody pool first!
        pool = self.nap.list_pool(schema, { 'id': self.pool_attrs['id'] })
        # first make sure our pool exists
        self.assertNotEqual(pool[0], [], 'Pool must exist!')
        pfxs = [
                '10.0.0.0/24',
                '10.0.1.0/24',
                '10.0.2.0/24',
                '10.0.3.0/24',
                '10.0.4.0/24'
                ]
        for p in pfxs:
            prefix_attrs = {
                    'authoritative_source': 'nap-test',
                    'prefix': p,
                    'description': 'test prefix',
                    'pool_id': self.pool_attrs['id'],
                    'comment': 'test comment, please remove! ;)'
                    }
            self.nap.add_prefix(schema, prefix_attrs)

        # get an address based on from-prefix
        prefix_attrs = {
                'authoritative_source': 'nap-test',
                'description': 'test prefix',
                'comment': 'test comment, please remove! ;)'
                }
        res = self.nap.add_prefix(schema, prefix_attrs, {'from-prefix': ['10.0.0.0/24'], 'prefix_length': 30 })
        p = self.nap.list_prefix(schema, { 'id': res })
        self.assertEqual(p[0]['prefix'], '10.0.0.0/30', "New prefix differ from what it should be!")

        self.nap.add_schema({ 'name': 'testtest', 'description': 'another test schema!' })
        # pass different schemas in attr and args
        # TODO: Find something similar?
        #self.assertRaises(nap.NapInputError, self.nap.add_prefix, schema, { 'authoritative_source': 'nap-test', 'description': 'tjong' }, { 'from-prefix': ['10.0.0.0/24'], 'prefix_length': 30 })



    def test_prefix_search_simple(self):
        """ Test the simple prefix search function.
        """

        schema = {'id': self.schema_attrs['id']}

        # First, perform e few tests to verify search string expansion.
        query_keys = dict()
        query_keys['testing testing'] = "description"
        query_keys['1.2.3.4'] = "prefix"

        # build query string
        query_str = ""
        for key, val in query_keys.items():
            if val == "description":
                query_str += "\"%s\" " % key
            else:
                query_str += "%s " % key

        res = self.nap.smart_search_prefix(schema, query_str)
        for interp in res['interpretation']:
            self.assertEqual(interp['string'] in query_keys, True, "Function returned unknown interpreted string %s" % interp['string'])

        prefix_attrs = {
                'authoritative_source': 'nap-test',
                'prefix': '1.3.3.77/32',
                'description': 'test-ish prefix',
                'comment': 'Test prefix #77! ;)'
                }

        self.nap.add_prefix(schema, prefix_attrs)
        res = self.nap.smart_search_prefix(schema, r"""1.3.3.77 "-ish" """)
        self.assertEqual(res['result'][-1]['prefix'], '1.3.3.77/32', 'Prefix not found')



    def test_prefix_remove(self):
        """ Remove a prefix
        """
        schema = {'id': self.schema_attrs['id']}
        prefix = self.nap.list_prefix(schema, { 'id': self.prefix_attrs['id'] })
        # first make sure our prefix exists
        self.assertEqual(prefix[0]['id'], self.prefix_attrs['id'], 'Record must exist before we can delete it')
        # remove the prefix, by id
        self.nap.remove_prefix(schema, { 'id': self.prefix_attrs['id'] })
        # check that search for old record doesn't return anything
        prefix = self.nap.list_prefix(schema, { 'id': self.prefix_attrs['id'] })
        self.assertEqual(prefix, [], 'Old entry still exists')


    def test_prefix_indent(self):
        """ Check that our indentation calculation is working

            Prefixes gets an indent value automatically assigned to help in
            displaying prefix information. The indent value is written on
            updates to the table and this test is to make sure it is correctly
            calculated.
        """
        schema = {'id': self.schema_attrs['id']}
        p1 = self.nap.list_prefix(schema, { 'prefix': '1.3.3.1/32' })[0]
        p2 = self.nap.list_prefix(schema, { 'prefix': '1.3.3.0/24' })[0]
        p3 = self.nap.list_prefix(schema, { 'prefix': '1.3.0.0/16' })[0]
        self.assertEqual(p1['indent'], 2, "Indent calc on add failed")
        self.assertEqual(p2['indent'], 1, "Indent calc on add failed")
        self.assertEqual(p3['indent'], 0, "Indent calc on add failed")
        # remove middle prefix
        self.nap.remove_prefix(schema, { 'id': self.prefix_attrs2['id'] })
        # check that child prefix indent level has decreased
        p1 = self.nap.list_prefix(schema, { 'prefix': '1.3.3.1/32' })[0]
        p3 = self.nap.list_prefix(schema, { 'prefix': '1.3.0.0/16' })[0]
        self.assertEqual(p1['indent'], 1, "Indent calc on remove failed")
        self.assertEqual(p3['indent'], 0, "Indent calc on remove failed")



    def test_find_free_prefix_input(self):
        """ Mostly input testing of find_free_prefix

            Try to stress find_free_prefix and send a lot of junk..
        """
        schema = {'id': self.schema_attrs['id']}
        # set up a prefix not used elsewhere so we have a known good state
        prefix_attrs = {
                'authoritative_source': 'nap-test',
                'prefix': '100.0.0.0/16',
                'description': 'test prefix',
                'comment': 'test comment, please remove! ;)'
                }
        self.nap.add_prefix(schema, prefix_attrs)

        # no schema, should raise error!
        self.assertRaises(nap.NapInputError, self.nap.find_free_prefix, schema, { 'from-prefix': ['100.0.0.0/16'] })

        # incorrect from-prefix type, string instead of list of strings (looking like an IP address)
        self.assertRaises(nap.NapInputError, self.nap.find_free_prefix, schema, { 'from-prefix': '100.0.0.0/16' })

        # missing prefix_length
        self.assertRaises(nap.NapMissingInputError, self.nap.find_free_prefix, schema, { 'from-prefix': [ '100.0.0.0/16' ], 'count': 1 })

        # try giving both IPv4 and IPv6 in from-prefix which shouldn't work
        self.assertRaises(nap.NapInputError, self.nap.find_free_prefix, schema, { 'from-prefix': [ '100.0.0.0/16', '2a00:800::0/25' ], 'prefix_length': 24, 'count': 1 })

        # try giving non-integer as wanted prefix length
        self.assertRaises(nap.NapValueError, self.nap.find_free_prefix, schema, { 'from-prefix': [ '100.0.0.0/16'], 'prefix_length': '24', 'count': 1 })

        # try giving to high a number as wanted prefix length for IPv4
        self.assertRaises(nap.NapValueError, self.nap.find_free_prefix, schema, { 'from-prefix': [ '100.0.0.0/16'], 'prefix_length': 35, 'count': 1 })

        # try giving to high a number as wanted prefix length for IPv6
        self.assertRaises(nap.NapValueError, self.nap.find_free_prefix, schema, { 'from-prefix': [ '2a00:800::1/25'], 'prefix_length': 150, 'count': 1 })

        # try giving a high number for result count (max is 1000)
        self.assertRaises(nap.NapValueError, self.nap.find_free_prefix, schema, { 'from-prefix': [ '100.0.0.0/16'], 'prefix_length': 30, 'count': 55555 })

        # don't pass 'family', which is required when specifying 'from-pool'
        self.assertRaises(nap.NapMissingInputError, self.nap.find_free_prefix, schema, { 'from-pool': { 'name': self.pool_attrs['name'] }, 'prefix_length': 24, 'count': 1 })

        # pass crap as family, wrong type even
        self.assertRaises(ValueError, self.nap.find_free_prefix, schema, { 'from-pool': { 'name': self.pool_attrs['name'] }, 'prefix_length': 24, 'count': 1, 'family': 'crap' })

        # pass 7 as family
        self.assertRaises(nap.NapValueError, self.nap.find_free_prefix, schema, { 'from-pool': { 'name': self.pool_attrs['name'] }, 'prefix_length': 24, 'count': 1, 'family': 7 })

        # pass non existent pool
        self.assertRaises(nap.NapNonExistentError, self.nap.find_free_prefix, schema, { 'from-pool': { 'name': 'crap' }, 'prefix_length': 24, 'count': 1, 'family': 4 })



    def test_find_free_prefix1(self):
        """ Functionality testing of find_free_prefix

            Mostly based on 'from-prefix'
        """
        schema = { 'id': self.schema_attrs['id'] }
        # set up a prefix not used elsewhere so we have a known good state
        prefix_attrs = {
                'authoritative_source': 'nap-test',
                'prefix': '100.0.0.0/16',
                'description': 'test prefix',
                'comment': 'test comment, please remove! ;)'
                }
        self.nap.add_prefix(schema, prefix_attrs)

        # simple test
        res = self.nap.find_free_prefix(schema, { 'from-prefix': [ '100.0.0.0/16', '1.3.3.0/24' ], 'prefix_length': 24, 'count': 1 })
        self.assertEqual(res, ['100.0.0.0/24'], "Incorrect prefix set returned")

        # simple test - only one input prefix (which did cause a bug, thus keeping it)
        res = self.nap.find_free_prefix(schema, { 'from-prefix': [ '100.0.0.0/16' ], 'prefix_length': 24, 'count': 1 })
        self.assertEqual(res, ['100.0.0.0/24'], "Incorrect prefix set returned")

        res = self.nap.find_free_prefix(schema, { 'from-prefix': [ '100.0.0.0/16', '1.3.3.0/24' ], 'prefix_length': 24, 'count': 999 })
        self.assertEqual(len(res), 256, "Incorrect prefix set returned")



    def test_find_free_prefix2(self):
        """ Functionality testing of find_free_prefix

            Mostly based on 'from-pool'
        """
        schema = { 'id': self.schema_attrs['id'] }
        # we need a bloody pool first!
        pool = self.nap.list_pool(schema, { 'id': self.pool_attrs['id'] })
        # first make sure our pool exists
        self.assertNotEqual(pool[0], [], 'Pool must exist!')
        pfxs = [
                '10.0.0.0/24',
                '10.0.1.0/24',
                '10.0.2.0/24',
                '10.0.3.0/24',
                '10.0.4.0/24'
                ]
        for p in pfxs:
            prefix_attrs = {
                    'authoritative_source': 'nap-test',
                    'prefix': p,
                    'description': 'test prefix',
                    'pool_id': self.pool_attrs['id'],
                    'comment': 'test comment, please remove! ;)'
                    }
            self.nap.add_prefix(schema, prefix_attrs)

        # from-pool test
        res = self.nap.find_free_prefix(schema, { 'from-pool': { 'name': self.pool_attrs['name'] }, 'count': 1, 'family': 4})
        self.assertEqual(res, ['10.0.1.0/30'], "Incorrect prefix set returned when requesting default prefix-length")

        # from-pool test, specify wanted prefix length
        res = self.nap.find_free_prefix(schema, { 'from-pool': { 'name': self.pool_attrs['name'] }, 'count': 1, 'family': 4, 'prefix_length': 31})
        self.assertEqual(res, ['10.0.1.0/31'], "Incorrect prefix set returned with explicit prefix-length")



def test_edit_prefix(self):
    """ Functionality testing of edit_prefix.
    """

    schema = { 'id': self.schema_attrs['id'] }
    data = { 
        'prefix': '192.0.2.0/24', 
        'description': 'foo',
        'comment': 'bar',
        'span_order': 0xBEEF,
        'alarm_priority': 'low',
        'type': 'assignment',
        'node': 'TOK-CORE-1',
        'country': 'EE',
        'authoritative_source': 'unittest',
        'pool': self.pool_attrs['id']
        }

    # basic edit
    self.nap.edit_prefix(schema, { 'id': self.prefix_attrs['id'] }, data)
    p = self.nap.list_prefix(schema, {'id': self.prefix_attrs['id']})[0]
    # remove what we did not touch
    for k, v in data.keys():
        if k not in p:
            del p[k]
    self.assertEqual(data, p, "Prefix data incorrect after edit.")

    # create a collision
    self.assertRaises(nap.NapError, self.nap.edit_prefix, schema, {'id': self.prefix_attrs2['id']}, {'prefix': data['prefix']})

    # try to change schema - disallowed
    self.assertRaises(nap.NapExtraneousInputError, self.nap_edit_prefix, schema, {'id': self.prefix_attrs2['id']}, {'schema': self.schema_attrs2['id']})



def main():
    if sys.version_info >= (2,7):
        unittest.main(verbosity=2)
    else:
        unittest.main()




if __name__ == '__main__':
    main()
