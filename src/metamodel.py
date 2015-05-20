# -*- coding: utf-8 -*-

#   Copyright (c) 2010-2014, MIT Probabilistic Computing Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Metamodel interface."""

import bayeslite.core as core

def bayesdb_register_metamodel(bdb, metamodel):
    """Register `metamodel` in `bdb`, creating any necessary tables.

    `metamodel` must not already be registered in any BayesDB, nor any
    metamodel by the same name.
    """
    name = metamodel.name()
    if name in bdb.metamodels:
        raise ValueError('Metamodel already registered: %s' % (name,))
    with bdb.savepoint():
        metamodel.register(bdb)
        bdb.metamodels[name] = metamodel

def bayesdb_deregister_metamodel(bdb, metamodel):
    """Deregister `metamodel`, which must have been registered in `bdb`."""
    name = metamodel.name()
    assert name in bdb.metamodels
    assert bdb.metamodels[name] == metamodel
    del bdb.metamodels[name]

class IBayesDBMetamodel(object):
    """BayesDB metamodel interface.

    Subclasses of :class:`IBayesDBMetamodel` implement the
    functionality needed by probabilistic BQL queries to sample from
    and inquire about the posterior distribution of a generative model
    conditioned on data in a table.  Instances of subclasses of
    `IBayesDBMetamodel` contain any in-memory state associated with
    the metamodel in the database.
    """

    def name(self):
        """Return the name of the metamodel as a str."""
        raise NotImplementedError

    def register(self, bdb):
        """Install any state needed for the metamodel in `bdb`.

        Called by :func:`bayeslite.bayesdb_register_metamodel`.

        Normally this will create SQL tables if necessary.
        """
        raise NotImplementedError

    def create_generator(self, bdb, table, schema, instantiate):
        """Create a generator for a table with the given schema.

        Called when executing ``CREATE GENERATOR``.

        Must parse `schema` to determine the column names and
        statistical types of the generator, and then call
        `instantiate` with a list of ``(column_name, stattype)``
        pairs.  `instantiate` will return a generator id and a list of
        ``(colno, column_name, stattype)`` triples.

        The generator id and column numbers may be used to create
        metamodel-specific records in the database for the generator
        with foreign keys referring to the ``bayesdb_generator`` and
        ``bayesdb_generator_column`` tables.

        `schema` is a list of schema items corresponding to the
        comma-separated ‘columns’ from a BQL ``CREATE GENERATOR``
        command.  Each schema item is a list of strings or lists of
        schema items, corresponding to whitespace-separated tokens and
        parenthesized lists.  Note that within parenthesized lists,
        commas are not excluded.
        """
        raise NotImplementedError

    def drop_generator(self, bdb, generator_id):
        """Drop any metamodel-specific records for a generator.

        Called when executing ``DROP GENERATOR``.
        """
        raise NotImplementedError

    def rename_column(self, bdb, generator_id, oldname, newname):
        """Note that a table column has been renamed.

        Not currently used.  To be used in the future when executing::

            ALTER TABLE <table> RENAME COLUMN <oldname> TO <newname>
        """
        raise NotImplementedError

    def initialize_models(self, bdb, generator_id, modelnos, model_config):
        """Initialize the specified model numbers for a generator."""
        raise NotImplementedError

    def drop_models(self, bdb, generator_id, modelnos=None):
        """Drop the specified model numbers of a generator.

        If none are specified, drop all models.
        """
        raise NotImplementedError

    def analyze_models(self, bdb, generator_id, modelnos=None, iterations=1,
            max_seconds=None, iterations_per_checkpoint=None):
        """Analyze the specified model numbers of a generator.

        If none are specified, analyze all of them.

        :param int iterations: maximum number of iterations of analysis for
            each model
        :param int max_seconds: requested maximum number of seconds to analyze
        :param int iterations_per_checkpoint: number of iterations before
            committing results of analysis to the database
        """
        raise NotImplementedError

    def column_dependence_probability(self, bdb, generator_id, colno0, colno1):
        """Compute ``DEPENDENCE PROBABILITY OF <col0> WITH <col1>``."""
        raise NotImplementedError

    def mutual_information(self, bdb, generator_id, colno0, colno1,
            numsamples=100):
        """Compute ``MUTUAL INFORMATION OF <col0> WITH <col1>``."""
        raise NotImplementedError

    def column_typicality(self, bdb, generator_id, colno):
        """Compute ``TYPICALITY OF <col>``."""
        raise NotImplementedError

    def column_value_probability(self, bdb, generator_id, colno, value):
        """Compute ``PROBABILITY OF <col> = <value>``."""
        raise NotImplementedError

    def row_similarity(self, bdb, generator_id, rowid, target_rowid, colnos):
        """Compute ``SIMILARITY TO <target_row>`` for given `rowid`."""
        raise NotImplementedError

    def row_typicality(self, bdb, generator_id, rowid):
        """Compute ``TYPICALITY`` for given `rowid`."""
        raise NotImplementedError

    def row_column_predictive_probability(self, bdb, generator_id, rowid,
            colno):
        """Compute ``PREDICTIVE PROBABILITY OF <col>`` for given `rowid`.

        If the row's value for that column is null, the result should
        be null (i.e., Python `None`).
        """
        raise NotImplementedError

    def predict(self, bdb, generator_id, colno, rowid, threshold,
            numsamples=None):
        """Predict a value for a column, if confidence is high enough."""
        value, confidence = self.predict_confidence(bdb, generator_id, colno,
            rowid, numsamples=numsamples)
        if confidence < threshold:
            return None
        return value

    def predict_confidence(self, bdb, generator_id, colno, rowid,
            numsamples=None):
        """Predict a value for a column and return confidence."""
        raise NotImplementedError

    def simulate(self, bdb, generator_id, constraints, colnos,
            numpredictions=1):
        """Simulate `colnos` from a generator, subject to `constraints`.

        Returns a list of rows with values for the specified columns.

        `colnos` is a list of column numbers.

        `constraints` is a list of ``(colno, value)`` pairs.

        `numpredictions` is the number of results to return.
        """
        raise NotImplementedError

    def insertmany(self, bdb, generator_id, rows):
        """Insert `rows` into a generator, updating analyses accordingly.

        `rows` is a list of tuples with one value for each column
        modelled by the generator.
        """
        raise NotImplementedError
