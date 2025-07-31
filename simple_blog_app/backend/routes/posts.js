

const express = require('express');
const router = express.Router();

router.route('/').get((req, res) => { res.send('GET /posts called!') });

router.route('/create').post((req, res) => { res.send('POST /posts/create called!') });

router.route('/:id').get((req, res) => { res.send('GET /posts/:id called!') });

router.route('/:id').put((req, res) => { res.send('PUT /posts/:id called!') });

router.route('/:id').delete((req, res) => { res.send('DELETE /posts/:id called!') });

module.exports = router;

