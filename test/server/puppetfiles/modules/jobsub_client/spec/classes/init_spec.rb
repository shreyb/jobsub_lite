require 'spec_helper'
describe 'jobsub_client' do
  context 'with default values for all parameters' do
    it { should contain_class('jobsub_client') }
  end
end
