const functions = require('firebase-functions');
const admin = require('firebase-admin');
const serviceAccount = require("../serviceAccountKey.json");
admin.initializeApp({
    credential: admin.credential.cert(serviceAccount)
});

// Attach a Firestore onCreate trigger
exports.sendNotificationOnCreate = functions.firestore
    .document('my_collection/{documentId}')
    .onCreate((snap, context) => {

        // Get the data from the newly created document
        const data = snap.data();

        // Send a notification using Firebase Cloud Messaging
        const payload = {
            notification: {
                title: 'New document added to my_collection',
                body: `Document ID: ${context.params.documentId}`
            }
        };

        return admin.messaging().sendToTopic('my_topic', payload);
    });
