import { initializeApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from 'firebase/auth'
import { getFirestore, collection, doc, setDoc, getDocs, onSnapshot } from 'firebase/firestore'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyDemoPlaceholderApiKeyForChameleon",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "chameleon-soc-demo.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "chameleon-soc-demo",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "chameleon-soc-demo.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "123456789012",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:123456789012:web:demo1234567890"
}

// Initialize Firebase
const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
export const googleProvider = new GoogleAuthProvider()
export const db = getFirestore(app)

export const signInWithGoogle = async () => {
  try {
    const result = await signInWithPopup(auth, googleProvider)
    const token = await result.user.getIdToken()
    return { user: result.user, token }
  } catch (error) {
    console.error("Google Sign-In Error:", error)
    throw error
  }
}

export const logOut = () => signOut(auth)
