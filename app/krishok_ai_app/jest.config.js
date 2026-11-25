module.exports = {
  preset: 'jest-expo',
  testMatch: ['**/?(*.)+(spec|test).[jt]s?(x)'],
  moduleNameMapper: { '^@/(.*)$': '<rootDir>/src/$1' },
  clearMocks: true,
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
};
