import React, { useState } from 'react';
import { Heart, Star, ShoppingCart, Bell, Settings, User, ChevronRight, Zap, Code, Palette } from 'lucide-react';

const TailwindSample = () => {
  const [activeTab, setActiveTab] = useState('colors');
  const [isCardHovered, setIsCardHovered] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-lg border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-2">
              <Palette className="h-8 w-8 text-indigo-600" />
              <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Tailwind CSS Demo
              </h1>
            </div>
            <nav className="hidden md:flex space-x-8">
              <a href="#" className="text-gray-600 hover:text-indigo-600 transition-colors">Components</a>
              <a href="#" className="text-gray-600 hover:text-indigo-600 transition-colors">Utilities</a>
              <a href="#" className="text-gray-600 hover:text-indigo-600 transition-colors">Examples</a>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-5xl font-extrabold text-gray-900 mb-6">
            Beautiful Design with
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
              Tailwind CSS
            </span>
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Rapidly build modern websites without ever leaving your HTML. A utility-first CSS framework packed with classes like flex, pt-4, text-center and rotate-90.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button className="bg-indigo-600 text-white px-8 py-3 rounded-lg hover:bg-indigo-700 transform hover:scale-105 transition-all duration-200 shadow-lg">
              Get Started
            </button>
            <button className="border-2 border-indigo-600 text-indigo-600 px-8 py-3 rounded-lg hover:bg-indigo-600 hover:text-white transition-all duration-200">
              View Examples
            </button>
          </div>
        </div>
      </section>

      {/* Tabs Navigation */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-12">
        <div className="flex flex-wrap justify-center gap-4 mb-8">
          {[
            { id: 'colors', label: 'Colors', icon: Palette },
            { id: 'layout', label: 'Layout', icon: Code },
            { id: 'components', label: 'Components', icon: Zap }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-6 py-3 rounded-lg transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-indigo-600 text-white shadow-lg transform scale-105'
                  : 'bg-white text-gray-600 hover:bg-gray-50 shadow-md'
              }`}
            >
              <tab.icon className="h-5 w-5" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Colors Tab */}
        {activeTab === 'colors' && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Color Palette</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4 mb-8">
              {[
                'bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-green-500',
                'bg-blue-500', 'bg-indigo-500', 'bg-purple-500', 'bg-pink-500'
              ].map((color, index) => (
                <div key={index} className="text-center">
                  <div className={`${color} w-16 h-16 rounded-lg mx-auto mb-2 shadow-lg hover:scale-110 transition-transform cursor-pointer`}></div>
                  <p className="text-sm text-gray-600">{color.replace('bg-', '')}</p>
                </div>
              ))}
            </div>
            
            {/* Gradient Examples */}
            <h4 className="text-xl font-semibold text-gray-900 mb-4">Gradients</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gradient-to-r from-pink-500 to-rose-500 p-6 rounded-lg text-white">
                <h5 className="font-semibold">Pink to Rose</h5>
                <p className="text-sm opacity-90">from-pink-500 to-rose-500</p>
              </div>
              <div className="bg-gradient-to-r from-blue-500 to-cyan-500 p-6 rounded-lg text-white">
                <h5 className="font-semibold">Blue to Cyan</h5>
                <p className="text-sm opacity-90">from-blue-500 to-cyan-500</p>
              </div>
              <div className="bg-gradient-to-r from-purple-500 to-indigo-500 p-6 rounded-lg text-white">
                <h5 className="font-semibold">Purple to Indigo</h5>
                <p className="text-sm opacity-90">from-purple-500 to-indigo-500</p>
              </div>
            </div>
          </div>
        )}

        {/* Layout Tab */}
        {activeTab === 'layout' && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Layout Examples</h3>
            
            {/* Flexbox Example */}
            <div className="mb-8">
              <h4 className="text-xl font-semibold text-gray-900 mb-4">Flexbox Layout</h4>
              <div className="flex flex-wrap gap-4 p-6 bg-gray-50 rounded-lg">
                <div className="flex-1 min-w-48 bg-blue-500 text-white p-4 rounded-lg text-center">Flex Item 1</div>
                <div className="flex-1 min-w-48 bg-green-500 text-white p-4 rounded-lg text-center">Flex Item 2</div>
                <div className="flex-1 min-w-48 bg-purple-500 text-white p-4 rounded-lg text-center">Flex Item 3</div>
              </div>
            </div>

            {/* Grid Example */}
            <div className="mb-8">
              <h4 className="text-xl font-semibold text-gray-900 mb-4">CSS Grid Layout</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6 bg-gray-50 rounded-lg">
                {[1, 2, 3, 4, 5, 6].map((item) => (
                  <div key={item} className="bg-indigo-500 text-white p-6 rounded-lg text-center font-semibold">
                    Grid Item {item}
                  </div>
                ))}
              </div>
            </div>

            {/* Responsive Example */}
            <div>
              <h4 className="text-xl font-semibold text-gray-900 mb-4">Responsive Design</h4>
              <div className="bg-gray-50 p-6 rounded-lg">
                <div className="bg-orange-500 text-white p-4 rounded-lg text-center sm:bg-green-500 md:bg-blue-500 lg:bg-purple-500">
                  <p className="font-semibold">Responsive Colors:</p>
                  <p className="text-sm">Orange (default) → Green (sm) → Blue (md) → Purple (lg)</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Components Tab */}
        {activeTab === 'components' && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Component Examples</h3>
            
            {/* Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              <div 
                className="bg-white border border-gray-200 rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden hover:-translate-y-2"
                onMouseEnter={() => setIsCardHovered(true)}
                onMouseLeave={() => setIsCardHovered(false)}
              >
                <div className="h-48 bg-gradient-to-br from-blue-500 to-purple-600"></div>
                <div className="p-6">
                  <h5 className="text-xl font-semibold text-gray-900 mb-2">Beautiful Card</h5>
                  <p className="text-gray-600 mb-4">This card has hover effects, shadows, and smooth transitions.</p>
                  <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                    Learn More
                  </button>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden hover:-translate-y-2">
                <div className="h-48 bg-gradient-to-br from-green-500 to-teal-600"></div>
                <div className="p-6">
                  <h5 className="text-xl font-semibold text-gray-900 mb-2">Interactive Card</h5>
                  <p className="text-gray-600 mb-4">Hover and focus states make interactions delightful.</p>
                  <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors">
                    Explore
                  </button>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 overflow-hidden hover:-translate-y-2">
                <div className="h-48 bg-gradient-to-br from-pink-500 to-rose-600"></div>
                <div className="p-6">
                  <h5 className="text-xl font-semibold text-gray-900 mb-2">Stunning Card</h5>
                  <p className="text-gray-600 mb-4">All built with utility classes, no custom CSS needed.</p>
                  <button className="bg-pink-600 text-white px-4 py-2 rounded-lg hover:bg-pink-700 transition-colors">
                    Discover
                  </button>
                </div>
              </div>
            </div>

            {/* Buttons */}
            <div className="mb-8">
              <h4 className="text-xl font-semibold text-gray-900 mb-4">Button Styles</h4>
              <div className="flex flex-wrap gap-4">
                <button className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors">Primary</button>
                <button className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors">Secondary</button>
                <button className="border-2 border-blue-600 text-blue-600 px-6 py-3 rounded-lg hover:bg-blue-600 hover:text-white transition-all">Outline</button>
                <button className="text-blue-600 px-6 py-3 rounded-lg hover:bg-blue-50 transition-colors">Ghost</button>
                <button className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-3 rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all">Gradient</button>
              </div>
            </div>

            {/* Form Elements */}
            <div>
              <h4 className="text-xl font-semibold text-gray-900 mb-4">Form Elements</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                  <input 
                    type="email" 
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    placeholder="you@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Select Option</label>
                  <select className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all">
                    <option>Choose an option</option>
                    <option>Option 1</option>
                    <option>Option 2</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Animations Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-12">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">Animations & Effects</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-500 rounded-full mx-auto mb-4 animate-bounce"></div>
              <p className="text-gray-600">animate-bounce</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-500 rounded-full mx-auto mb-4 animate-spin"></div>
              <p className="text-gray-600">animate-spin</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-500 rounded-full mx-auto mb-4 animate-pulse"></div>
              <p className="text-gray-600">animate-pulse</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h3 className="text-2xl font-bold mb-4">Ready to build amazing things?</h3>
            <p className="text-gray-400 mb-6">Tailwind CSS makes it easy to create beautiful, responsive designs.</p>
            <button className="bg-indigo-600 text-white px-8 py-3 rounded-lg hover:bg-indigo-700 transition-colors">
              Start Building
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default TailwindSample; 