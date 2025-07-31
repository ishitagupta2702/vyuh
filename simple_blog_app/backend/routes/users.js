

const express = require('express');
const router = express.Router();

router.route('/').get((req, res) => { res.send('GET /users called!') });

router.route('/register').post((req, res) => { res.send('POST /users/register called!') });

router.route('/login').post((req, res) => { res.send('POST /users/login called!') });

module.exports = router;

