import "@testing-library/jest-dom";

// jsdom doesn't implement fetch; tests provide their own mock implementation
// via jest.spyOn(global, "fetch"), which requires the property to exist first.
if (!global.fetch) {
  global.fetch = jest.fn();
}
