import { detectionHistoryRepository } from '../historyRepository';
import { preferencesRepository } from '../preferencesRepository';

jest.mock('../localDatabase', () => ({ getLocalDatabase: jest.fn() }));

const mockDb = {
  runAsync: jest.fn(),
  getAllAsync: jest.fn(),
  getFirstAsync: jest.fn(),
  execAsync: jest.fn(),
};
const getDb = jest.mocked(require('../localDatabase').getLocalDatabase) as jest.Mock;

describe('SQLite repositories', () => {
  beforeEach(() => {
    getDb.mockResolvedValue(mockDb);
  });

  it('saves preferences with a parameterized SQLite upsert', async () => {
    await preferencesRepository.set('language', 'bn');
    expect(mockDb.runAsync).toHaveBeenCalledWith(
      expect.stringContaining('INSERT INTO app_preferences'),
      'language',
      'bn',
    );
  });

  it('maps and orders SQLite history rows into domain records', async () => {
    mockDb.getAllAsync.mockResolvedValue([
      {
        id: 9,
        image_uri: 'file://leaf.jpg',
        created_at: '2026-11-25T10:00:00.000Z',
        predicted_class_id: 4,
        confidence: 0.93,
        mode: 'offline',
      },
    ]);
    await expect(detectionHistoryRepository.list()).resolves.toEqual([
      {
        id: 9,
        imageUri: 'file://leaf.jpg',
        createdAt: '2026-11-25T10:00:00.000Z',
        predictedClassId: 4,
        confidence: 0.93,
        mode: 'offline',
      },
    ]);
    expect(mockDb.getAllAsync).toHaveBeenCalledWith(
      expect.stringContaining('ORDER BY created_at DESC'),
    );
  });

  it('clears detection history', async () => {
    await detectionHistoryRepository.clear();
    expect(mockDb.runAsync).toHaveBeenCalledWith('DELETE FROM detection_history');
  });
});
