class StreamAudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffers = [];
  }

  process(inputs, outputs) {
    const output = outputs[0];
    const channelData = output[0];

    if (this.buffers.length === 0) return true;

    const currentBuffer = this.buffers.shift();
    channelData.set(currentBuffer);

    return true;
  }

  static get parameterDescriptors() {
    return [];
  }
}

registerProcessor('stream-audio-processor', StreamAudioProcessor); 