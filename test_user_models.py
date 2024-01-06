# run these tests like:
# python -m unittest test_user_models.py

import os
from unittest import TestCase
from sqlalchemy import exc

from models import (db, User, Pod, SubPod, PodMessage, 
                    SubPodMessage, PodUser, SubPodUser,
                    Hobby, UserHobby, InvitedMembers, PreviouslyJoined)

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///peapods-test"

# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class UserModelTestCase(TestCase):
    '''Testing User '''

    def setUp(self):
        '''Creating a test client and sample data'''
        db.drop_all()
        db.create_all()

        u1 = User.signup('catdog', 'password', 'catdog', 'tails', 'catdog@email.com', 'Rochester', 'MN')
        u_id = 1111
        u1.id = u_id

        db.session.commit()

        u1 = User.query.get(u_id)

        self.u1 = u1
        self.u_id = u_id

        self.client = app.test_client()

    def tearDown(self) -> None:
        res = super().tearDown()
        db.session.rollback()
        return res
    
    def test_create_user(self):
        new_user = User()
        


