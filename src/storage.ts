import AsyncStorage from '@react-native-async-storage/async-storage';
import { decodeState, State } from './model';
export const STORAGE_KEY = 'thank-you.learning.v1';
export async function loadState() { return decodeState(await AsyncStorage.getItem(STORAGE_KEY)); }
export async function saveState(state: State) { await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
